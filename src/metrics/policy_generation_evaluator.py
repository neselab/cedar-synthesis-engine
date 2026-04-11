from __future__ import annotations

import importlib.util
import json
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path


THIS_FILE = Path(__file__).resolve()
SRC_DIR = THIS_FILE.parent.parent

sys.path.insert(0, str(SRC_DIR))

from metrics.solver_wrapper import (  # noqa: E402
    CheckResult,
    run_always_denies_check,
    run_implies_check,
    run_never_errors_check,
    run_syntax_check,
)
from metrics.policy_generation_metrics import (  # noqa: E402
    RunMetricRecord,
    _classify_validation_failure,
    compute_run_metrics,
    metric_record_to_dict,
)
from metrics.error_explainer import explain_validation_error  # noqa: E402


def load_checks(workspace: str) -> list[dict]:
    """Load verification checks from workspace/verification_plan.py."""
    vp_path = str(Path(workspace) / "verification_plan.py")
    spec = importlib.util.spec_from_file_location("verification_plan", vp_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.get_checks()


@dataclass
class EvaluationStage:
    name: str
    passed: bool
    status: str
    message: str
    details: dict


@dataclass
class EvaluationBundle:
    workspace_path: str
    syntax_pass: bool
    schema_pass: bool
    semantic_accuracy: float
    verification_pass: bool
    loss: int
    total_check_count: int
    failed_checks: list[str]
    failed_check_types: list[str]
    metrics: dict
    verification: dict
    stages: list[dict]


def _run_semantic_checks(workspace_path: Path) -> tuple[list[CheckResult], float]:
    schema_path = workspace_path / "schema.cedarschema"
    candidate_path = workspace_path / "candidate.cedar"
    checks = load_checks(str(workspace_path))
    results: list[CheckResult] = []
    t0 = time.monotonic()

    for check in checks:
        ctype = check["type"]
        if ctype == "implies":
            result = run_implies_check(
                schema_path=str(schema_path),
                candidate_path=str(candidate_path),
                reference_path=check["reference_path"],
                principal_type=check["principal_type"],
                action=check["action"],
                resource_type=check["resource_type"],
                check_name=check["name"],
                description=check["description"],
            )
        elif ctype == "floor":
            result = run_implies_check(
                schema_path=str(schema_path),
                candidate_path=check["floor_path"],
                reference_path=str(candidate_path),
                principal_type=check["principal_type"],
                action=check["action"],
                resource_type=check["resource_type"],
                check_name=check["name"],
                description=check["description"],
            )
        elif ctype == "always-denies-liveness":
            result = run_always_denies_check(
                schema_path=str(schema_path),
                candidate_path=str(candidate_path),
                principal_type=check["principal_type"],
                action=check["action"],
                resource_type=check["resource_type"],
                check_name=check["name"],
                description=check["description"],
                expect_denies=False,
            )
        elif ctype == "never-errors":
            result = run_never_errors_check(
                schema_path=str(schema_path),
                candidate_path=str(candidate_path),
                principal_type=check["principal_type"],
                action=check["action"],
                resource_type=check["resource_type"],
            )
        else:
            continue
        results.append(result)

    return results, time.monotonic() - t0


def evaluate_workspace(workspace: str | Path, prompt_variant: str = "unknown") -> EvaluationBundle:
    """
    Evaluate a workspace in three sequential stages:

    1. syntax
    2. schema grounding
    3. semantic alignment

    Lower stages gate higher stages:
    - syntax fail => stop
    - schema fail => stop
    - semantic runs only after syntax/schema pass
    """
    workspace_path = Path(workspace).resolve()
    schema_path = workspace_path / "schema.cedarschema"
    candidate_path = workspace_path / "candidate.cedar"

    stages: list[EvaluationStage] = []

    is_valid, error_msg, _error_kind = run_syntax_check(str(schema_path), str(candidate_path))
    if not is_valid:
        syntax_error, schema_error = _classify_validation_failure(error_msg)
        if syntax_error:
            explanation = explain_validation_error(error_msg)
            stages.append(
                EvaluationStage(
                    name="syntax",
                    passed=False,
                    status="fail",
                    message="Cedar parsing/DSL validation failed.",
                    details={"error": error_msg, "explanation": explanation},
                )
            )
            stages.append(
                EvaluationStage(
                    name="schema",
                    passed=False,
                    status="skipped",
                    message="Skipped because syntax validation failed.",
                    details={},
                )
            )
            stages.append(
                EvaluationStage(
                    name="semantic",
                    passed=False,
                    status="skipped",
                    message="Skipped because syntax validation failed.",
                    details={},
                )
            )
        elif schema_error:
            explanation = explain_validation_error(error_msg)
            stages.append(
                EvaluationStage(
                    name="syntax",
                    passed=True,
                    status="pass",
                    message="Cedar parsing/DSL validation passed.",
                    details={},
                )
            )
            stages.append(
                EvaluationStage(
                    name="schema",
                    passed=False,
                    status="fail",
                    message="Schema grounding failed during Cedar validation.",
                    details={"error": error_msg, "explanation": explanation},
                )
            )
            stages.append(
                EvaluationStage(
                    name="semantic",
                    passed=False,
                    status="skipped",
                    message="Skipped because schema grounding failed.",
                    details={},
                )
            )
        else:
            explanation = explain_validation_error(error_msg)
            stages.append(
                EvaluationStage(
                    name="syntax",
                    passed=False,
                    status="fail",
                    message="Validation failed with an unclassified low-level error.",
                    details={"error": error_msg, "explanation": explanation},
                )
            )
            stages.append(
                EvaluationStage(
                    name="schema",
                    passed=False,
                    status="skipped",
                    message="Skipped because low-level validation failed.",
                    details={},
                )
            )
            stages.append(
                EvaluationStage(
                    name="semantic",
                    passed=False,
                    status="skipped",
                    message="Skipped because low-level validation failed.",
                    details={},
                )
            )

        pseudo_result = type("PseudoVR", (), {})()
        pseudo_result.loss = 1
        pseudo_result.results = [CheckResult(
            check_name="syntax",
            check_type="syntax",
            description="Cedar validation",
            passed=False,
            counterexample=error_msg,
        )]
        pseudo_result.solver_time_s = 0.0
        metric_record = compute_run_metrics(prompt_variant, pseudo_result)

        verification_blob = {
            "loss": 1,
            "solver_time_s": 0.0,
            "checks": [],
            "results": [asdict(pseudo_result.results[0])],
        }

        return EvaluationBundle(
            workspace_path=str(workspace_path),
            syntax_pass=metric_record.syntax_pass,
            schema_pass=metric_record.schema_pass,
            semantic_accuracy=metric_record.semantic_accuracy,
            verification_pass=False,
            loss=1,
            total_check_count=metric_record.total_check_count,
            failed_checks=["syntax"],
            failed_check_types=["syntax"],
            metrics=metric_record_to_dict(metric_record),
            verification=verification_blob,
            stages=[asdict(stage) for stage in stages],
        )

    stages.append(
        EvaluationStage(
            name="syntax",
            passed=True,
            status="pass",
            message="Cedar parsing/DSL validation passed.",
            details={},
        )
    )
    stages.append(
        EvaluationStage(
            name="schema",
            passed=True,
            status="pass",
            message="Schema grounding passed.",
            details={},
        )
    )

    semantic_results, solver_time = _run_semantic_checks(workspace_path)
    semantic_failed = [r for r in semantic_results if not r.passed]
    semantic_loss = len(semantic_failed)
    semantic_accuracy = (
        (len(semantic_results) - semantic_loss) / len(semantic_results)
        if semantic_results
        else 0.0
    )

    if semantic_loss == 0:
        stages.append(
            EvaluationStage(
                name="semantic",
                passed=True,
                status="pass",
                message="All semantic checks passed.",
                details={
                    "total_checks": len(semantic_results),
                    "solver_time_s": round(solver_time, 3),
                    "checks": [
                        {
                            "name": r.check_name,
                            "type": r.check_type,
                            "description": r.description,
                            "passed": r.passed,
                            "counterexample": r.counterexample,
                        }
                        for r in semantic_results
                    ],
                },
            )
        )
    else:
        stages.append(
            EvaluationStage(
                name="semantic",
                passed=False,
                status="fail",
                message="One or more semantic checks failed.",
                details={
                    "total_checks": len(semantic_results),
                    "failed_checks": [r.check_name for r in semantic_failed],
                    "solver_time_s": round(solver_time, 3),
                    "checks": [
                        {
                            "name": r.check_name,
                            "type": r.check_type,
                            "description": r.description,
                            "passed": r.passed,
                            "counterexample": r.counterexample,
                        }
                        for r in semantic_results
                    ],
                },
            )
        )

    vr = type("PseudoVR", (), {})()
    vr.loss = semantic_loss
    vr.results = semantic_results
    vr.solver_time_s = solver_time
    metric_record = compute_run_metrics(prompt_variant, vr)

    failed_checks = [r.check_name for r in semantic_failed]
    failed_check_types = [r.check_type for r in semantic_failed]

    verification_blob = {
        "loss": semantic_loss,
        "solver_time_s": round(solver_time, 3),
        "checks": load_checks(str(workspace_path))
        if (workspace_path / "verification_plan.py").exists()
        else [],
        "results": [asdict(r) for r in semantic_results],
    }

    return EvaluationBundle(
        workspace_path=str(workspace_path),
        syntax_pass=True,
        schema_pass=True,
        semantic_accuracy=round(semantic_accuracy, 4),
        verification_pass=(semantic_loss == 0),
        loss=semantic_loss,
        total_check_count=len(semantic_results),
        failed_checks=failed_checks,
        failed_check_types=failed_check_types,
        metrics=metric_record_to_dict(metric_record),
        verification=verification_blob,
        stages=[asdict(stage) for stage in stages],
    )


def write_evaluation_bundle(bundle: EvaluationBundle, output_path: str | Path) -> None:
    output = Path(output_path)
    output.write_text(json.dumps(asdict(bundle), indent=2))
