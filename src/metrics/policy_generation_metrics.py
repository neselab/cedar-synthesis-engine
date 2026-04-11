from __future__ import annotations

import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


THIS_FILE = Path(__file__).resolve()
SRC_DIR = THIS_FILE.parent.parent

sys.path.insert(0, str(SRC_DIR))

from metrics.solver_wrapper import VerificationResult


SYNTAX_PATTERNS = [
    r"failed to parse policy set",
    r"unexpected end of input",
    r"expected `",
    r"unexpected token",
    r"parse error",
]

SCHEMA_PATTERNS = [
    r"policy set validation failed",
    r"attribute `[^`]+` .* not found",
    r"entity type `[^`]+` not found",
    r"action `[^`]+` .* not found",
    r"not declared in the schema",
    r"does not apply to",
    r"type mismatch",
]

HALLUCINATED_IDENTIFIER_PATTERNS = [
    r"attribute `([^`]+)` on entity type `[^`]+` not found",
    r"(?:^|\n)\s*entity type `([^`]+)` not found",
    r"action `([^`]+)` .* not found",
]


@dataclass
class RunMetricRecord:
    prompt_variant: str
    syntax_pass: bool
    schema_pass: bool
    semantic_accuracy: float
    syntax_error: bool
    schema_error: bool
    semantic_error: bool
    syntax_error_rate: float
    schema_violation_rate: float
    hallucinated_identifier_rate: float
    hallucinated_identifier_count: int
    failed_check_count: int
    total_check_count: int
    primary_error_type: str
    validation_message: str


@dataclass
class StrategyMetricSummary:
    prompt_variant: str
    run_count: int
    syntax_pass_rate: float
    schema_pass_rate: float
    semantic_accuracy: float


def _matches_any(text: str, patterns: list[str]) -> bool:
    lowered = text.lower()
    return any(re.search(pattern, lowered) for pattern in patterns)


def _extract_hallucinated_identifier_count(text: str) -> int:
    count = 0
    for pattern in HALLUCINATED_IDENTIFIER_PATTERNS:
        count += len(re.findall(pattern, text, re.IGNORECASE))
    return count


def _classify_validation_failure(message: str) -> tuple[bool, bool]:
    """
    Returns:
      (syntax_error, schema_error)

    Notes:
    - Cedar validate covers both parse errors and schema-grounding failures.
    - We treat parse failures as syntax errors.
    - We treat validation failures against the schema as schema errors.
    """
    syntax_error = _matches_any(message, SYNTAX_PATTERNS)
    schema_error = (not syntax_error) and _matches_any(message, SCHEMA_PATTERNS)
    return syntax_error, schema_error


def compute_run_metrics(prompt_variant: str, vr: VerificationResult) -> RunMetricRecord:
    """
    Compute reusable policy-generation metrics from a verification result.

    Metric semantics:
    - SyntaxPass: candidate is parsable Cedar
    - SchemaPass: candidate grounds correctly against the schema
    - SemanticAccuracy: fraction of formal verification checks passed

    If Cedar validation fails before symbolic checking:
    - syntax/schema metrics are inferred from the validator message
    - semantic accuracy is set to 0.0
    """
    validation_message = ""
    if len(vr.results) == 1 and vr.results[0].check_type == "syntax" and not vr.results[0].passed:
        validation_message = vr.results[0].counterexample or ""
        syntax_error, schema_error = _classify_validation_failure(validation_message)
        syntax_pass = not syntax_error
        schema_pass = syntax_pass and not schema_error
        semantic_accuracy = 0.0
        semantic_error = False
        failed_check_count = 0
        total_check_count = 0
    else:
        syntax_error = False
        schema_error = False
        syntax_pass = True
        schema_pass = True
        total_check_count = len(vr.results)
        failed_check_count = sum(1 for r in vr.results if not r.passed)
        semantic_accuracy = (
            (total_check_count - failed_check_count) / total_check_count
            if total_check_count
            else 0.0
        )
        semantic_error = failed_check_count > 0

    hallucinated_identifier_count = _extract_hallucinated_identifier_count(validation_message)

    if syntax_error:
        primary_error_type = "syntax"
    elif schema_error:
        primary_error_type = "schema"
    elif semantic_error:
        primary_error_type = "semantic"
    else:
        primary_error_type = "none"

    return RunMetricRecord(
        prompt_variant=prompt_variant,
        syntax_pass=syntax_pass,
        schema_pass=schema_pass,
        semantic_accuracy=round(semantic_accuracy, 4),
        syntax_error=syntax_error,
        schema_error=schema_error,
        semantic_error=semantic_error,
        syntax_error_rate=1.0 if syntax_error else 0.0,
        schema_violation_rate=1.0 if schema_error else 0.0,
        hallucinated_identifier_rate=float(hallucinated_identifier_count),
        hallucinated_identifier_count=hallucinated_identifier_count,
        failed_check_count=failed_check_count,
        total_check_count=total_check_count,
        primary_error_type=primary_error_type,
        validation_message=validation_message,
    )


def aggregate_by_prompt_variant(records: Iterable[RunMetricRecord]) -> list[StrategyMetricSummary]:
    grouped: dict[str, list[RunMetricRecord]] = {}
    for record in records:
        grouped.setdefault(record.prompt_variant, []).append(record)

    summaries = []
    for variant, items in sorted(grouped.items()):
        run_count = len(items)
        summaries.append(
            StrategyMetricSummary(
                prompt_variant=variant,
                run_count=run_count,
                syntax_pass_rate=round(sum(r.syntax_pass for r in items) / run_count, 4),
                schema_pass_rate=round(sum(r.schema_pass for r in items) / run_count, 4),
                semantic_accuracy=round(sum(r.semantic_accuracy for r in items) / run_count, 4),
            )
        )
    return summaries


def metric_record_to_dict(record: RunMetricRecord) -> dict:
    return asdict(record)


def strategy_summary_to_dict(summary: StrategyMetricSummary) -> dict:
    return asdict(summary)
