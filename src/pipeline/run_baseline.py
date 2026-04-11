from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from openai import OpenAI


THIS_FILE = Path(__file__).resolve()
PIPELINE_DIR = THIS_FILE.parent
SRC_DIR = PIPELINE_DIR.parent
CEDARFORGE_DIR = SRC_DIR.parent
RUNS_DIR = SRC_DIR / "runs"

sys.path.insert(0, str(SRC_DIR))

from metrics.policy_generation_evaluator import evaluate_workspace  # noqa: E402
from metrics.policy_generation_metrics import (  # noqa: E402
    RunMetricRecord,
    aggregate_by_prompt_variant,
    strategy_summary_to_dict,
)


PROMPT_VARIANTS = [
    "zero_shot_direct",
    "structured_instruction",
    "cot",
    "few_shot_grounded",
]
PROMPT_STRATEGY_DIR = PIPELINE_DIR / "prompt_strategies"

# Temperature used for repair iterations (iteration > 1).
# Initial generation uses the caller-supplied temperature (default 0.0).
# Repair must use a higher value so the model can produce different outputs
# across iterations — at temperature=0 the model is fully deterministic and
# will repeat the same wrong candidate every time, making the repair loop
# pointless and triggering oscillation detection immediately.
REPAIR_TEMPERATURE = 0.4


@dataclass
class RunRecord:
    run_id: str
    task_id: str
    task_path: str
    prompt_variant: str
    model: str
    base_url: str
    syntax_pass: bool
    verification_pass: bool
    loss: int
    failed_checks: list[str]
    failed_check_types: list[str]
    duration_s: float
    metrics: dict
    raw_output_path: str
    candidate_path: str
    workspace_path: str
    log_path: str


@dataclass
class IterationRecord:
    iteration: int
    is_repair_iteration: bool
    prompt_variant: str
    syntax_pass: bool
    schema_pass: bool
    semantic_accuracy: float
    verification_pass: bool
    loss: int
    failed_checks: list[str]
    failed_check_types: list[str]
    duration_s: float
    metrics: dict
    raw_output_path: str
    candidate_path: str
    evaluation_bundle_path: str
    verification_result_path: str
    workspace_path: str
    prompt_path: str
    log_path: str


@dataclass
class RepairLoopRecord:
    run_id: str
    task_id: str
    task_path: str
    initial_prompt_variant: str
    model: str
    base_url: str
    max_iterations: int
    completed_iterations: int
    stop_reason: str
    final_syntax_pass: bool
    final_schema_pass: bool
    final_semantic_accuracy: float
    final_verification_pass: bool
    final_loss: int
    best_semantic_accuracy: float
    best_candidate_iteration: int | None
    first_success_iteration: int | None
    oscillation_count: int
    failure_layer_sequence: list[str]
    iterations: list[dict]


def _load_json(path: Path) -> dict:
    with path.open() as f:
        return json.load(f)


def _load_text(path: Path) -> str:
    with path.open() as f:
        return f.read().strip()


def _extract_cedar(text: str) -> str:
    text = text.strip()
    tagged = re.search(r"<cedar_policy>\s*(.*?)\s*</cedar_policy>", text, re.DOTALL | re.IGNORECASE)
    if tagged:
        return tagged.group(1).strip()
    block = re.search(r"```(?:cedar)?\s*(.*?)\s*```", text, re.DOTALL)
    if block:
        return block.group(1).strip()
    return text


def _copy_task_workspace(task_path: Path, dest: Path) -> Path:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)
    return dest


def _load_task_registry() -> dict[str, dict]:
    data = _load_json(PIPELINE_DIR / "tasks.json")
    return {task["id"]: task for task in data["tasks"]}


def _task_abs_path(task_rel_path: str) -> Path:
    return (CEDARFORGE_DIR / task_rel_path).resolve()


def _load_assets() -> dict[str, str]:
    assets_dir = PIPELINE_DIR / "prompt_assets"
    return {
        "cheat_sheet": _load_text(assets_dir / "cedar_syntax_cheat_sheet.md"),
        "skeleton": _load_text(assets_dir / "policy_skeleton.cedar"),
        "positive": _load_text(assets_dir / "few_shot_positive_example.md"),
    }


def _load_prompt_template(variant: str) -> str:
    prompt_path = PROMPT_STRATEGY_DIR / f"{variant}.md"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt strategy file not found: {prompt_path}")
    return _load_text(prompt_path)


def _build_prompt(variant: str, schema: str, policy_spec: str, assets: dict[str, str]) -> str:
    template = _load_prompt_template(variant)
    return template.format(
        CEDAR_SCHEMA=schema,
        POLICY_SPEC=policy_spec,
        CEDAR_SYNTAX_CHEAT_SHEET=assets["cheat_sheet"],
        POLICY_SKELETON=assets["skeleton"],
        FEW_SHOT_POSITIVE_EXAMPLE=assets["positive"],
    )


def _load_task_inputs(task_path: Path) -> tuple[str, str]:
    schema_path = task_path / "schema.cedarschema"
    if not schema_path.exists():
        schema_path = task_path / "policies.cedarschema"

    spec_path = task_path / "policy_spec.md"
    if not schema_path.exists():
        raise FileNotFoundError(f"No schema found in {task_path}")
    if not spec_path.exists():
        raise FileNotFoundError(f"No policy_spec.md found in {task_path}")

    return _load_text(schema_path), _load_text(spec_path)


def _call_model(base_url: str, model: str, prompt: str, temperature: float, max_tokens: int) -> str:
    client = OpenAI(base_url=base_url, api_key="EMPTY")
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are a careful Cedar policy generator. Output only final Cedar code."
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=temperature,
        max_tokens=max_tokens,
        extra_body={
            "chat_template_kwargs": {
                "enable_thinking": False,
            },
        },
    )
    return response.choices[0].message.content or ""


def _append_log(log_lines: list[str], line: str = "") -> None:
    log_lines.append(line)


def _print_and_log(log_lines: list[str], line: str = "") -> None:
    print(line)
    _append_log(log_lines, line)


def _shorten(text: str, max_len: int = 500) -> str:
    text = text.strip()
    if len(text) <= max_len:
        return text
    return text[:max_len].rstrip() + "\n...[truncated]..."


def _link_or_copy(src: Path, dst: Path) -> None:
    if dst.exists() or dst.is_symlink():
        if dst.is_dir() and not dst.is_symlink():
            shutil.rmtree(dst)
        else:
            dst.unlink()
    try:
        if src.is_dir():
            os.symlink(src, dst, target_is_directory=True)
        else:
            os.symlink(src, dst)
    except OSError:
        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)


def _prepare_eval_workspace(task_path: Path, eval_workspace: Path, candidate_text: str) -> Path:
    if eval_workspace.exists():
        shutil.rmtree(eval_workspace)
    eval_workspace.mkdir(parents=True, exist_ok=True)

    for name in ("schema.cedarschema", "policies.cedarschema", "policy_spec.md", "verification_plan.py", "policy_store.cedar"):
        src = task_path / name
        if src.exists():
            dst_name = "schema.cedarschema" if name == "policies.cedarschema" else name
            _link_or_copy(src, eval_workspace / dst_name)

    refs_src = task_path / "references"
    if refs_src.exists():
        _link_or_copy(refs_src, eval_workspace / "references")

    (eval_workspace / "candidate.cedar").write_text(candidate_text)
    return eval_workspace


def _get_failing_layer(bundle) -> str:
    """Return the highest-priority failing layer: syntax, schema, or semantic."""
    for stage in bundle.stages:
        if stage["name"] in ("syntax", "schema") and not stage["passed"] and stage["status"] == "fail":
            return stage["name"]
    for stage in bundle.stages:
        if stage["name"] == "semantic" and not stage["passed"]:
            return "semantic"
    return "none"


def _is_oscillating(candidate_hashes: list[str], failure_layer_sequence: list[str]) -> bool:
    """Detect oscillation: identical output as previous iteration, or syntax<->semantic cycling."""
    if len(candidate_hashes) >= 2 and candidate_hashes[-1] == candidate_hashes[-2]:
        return True
    if len(failure_layer_sequence) >= 4:
        recent = failure_layer_sequence[-4:]
        if recent in (
            ["syntax", "semantic", "syntax", "semantic"],
            ["semantic", "syntax", "semantic", "syntax"],
        ):
            return True
    return False


def _render_failure_feedback(bundle, task_path: Path) -> tuple[str, str]:
    """
    Build layered, directional feedback for the repair prompt.

    Returns (feedback_text, failing_layer) where failing_layer is one of:
      "syntax", "schema", "semantic"
    """
    failing_layer = _get_failing_layer(bundle)
    lines: list[str] = []

    if failing_layer == "syntax":
        stage = next(s for s in bundle.stages if s["name"] == "syntax")
        details = stage.get("details", {})
        lines.append("SYNTAX ERROR — Fix the syntax before addressing anything else.")
        lines.append("")
        explanation = details.get("explanation")
        if explanation:
            lines.append(f"Summary:       {explanation.get('summary', '')}")
            lines.append(f"Likely cause:  {explanation.get('likely_cause', '')}")
            lines.append(f"Suggested fix: {explanation.get('suggested_fix', '')}")
        if details.get("error"):
            lines.append("")
            lines.append("Raw error:")
            lines.append(_shorten(details["error"], 1200))
        lines.append("")
        lines.append("NOTE: Semantic counterexamples are omitted — they are irrelevant until syntax passes.")

    elif failing_layer == "schema":
        stage = next(s for s in bundle.stages if s["name"] == "schema")
        details = stage.get("details", {})
        lines.append("SCHEMA ERROR — The policy parses but uses identifiers not present in the schema.")
        lines.append("")
        explanation = details.get("explanation")
        if explanation:
            lines.append(f"Summary:       {explanation.get('summary', '')}")
            lines.append(f"Likely cause:  {explanation.get('likely_cause', '')}")
            lines.append(f"Suggested fix: {explanation.get('suggested_fix', '')}")
        if details.get("error"):
            lines.append("")
            lines.append("Raw error:")
            lines.append(_shorten(details["error"], 1200))
        lines.append("")
        lines.append("NOTE: Only fix identifier names. Do not change policy logic or conditions.")

    else:  # semantic
        stage = next(s for s in bundle.stages if s["name"] == "semantic")
        details = stage.get("details", {})
        checks = details.get("checks", [])
        failed_checks = [c for c in checks if not c["passed"]]

        # Load verification plan to get reference/floor paths
        vp_checks: dict[str, dict] = {}
        try:
            from metrics.policy_generation_evaluator import load_checks as _load_vp_checks
            for c in _load_vp_checks(str(task_path)):
                vp_checks[c["name"]] = c
        except Exception:
            pass

        lines.append(f"SEMANTIC FAILURE — {len(failed_checks)} of {len(checks)} check(s) failed.")
        lines.append("")

        for check in failed_checks:
            ctype = check["type"]
            cname = check["name"]
            lines.append(f"--- Check: {cname} [{ctype}] ---")
            lines.append(f"Description: {check['description']}")
            lines.append("")

            if ctype == "implies":
                lines.append("Direction: TIGHTEN — your policy permits requests that the ceiling forbids.")
                lines.append("Action: Add a condition or tighten the when-clause to block the counterexample request.")
            elif ctype == "floor":
                lines.append("Direction: RELAX — your policy denies requests that the floor requires to be permitted.")
                lines.append("Action: Add a permit rule or relax a condition to allow the counterexample request.")
            elif "liveness" in ctype:
                lines.append("Direction: ADD PERMIT — your policy always denies this action. Add a permit rule.")
            elif ctype == "never-errors":
                lines.append("Direction: FIX RUNTIME ERROR — your policy causes a runtime error on some input.")

            vp_check = vp_checks.get(cname, {})
            ref_path = vp_check.get("reference_path") or vp_check.get("floor_path")
            if ref_path:
                try:
                    ref_text = Path(ref_path).read_text().strip()
                    lines.append("")
                    lines.append(f"Reference policy ({Path(ref_path).name}):")
                    lines.append("```cedar")
                    lines.append(ref_text)
                    lines.append("```")
                except Exception:
                    pass

            if check.get("counterexample"):
                lines.append("")
                lines.append("Counterexample:")
                lines.append(_shorten(check["counterexample"], 1000))
            lines.append("")

    return "\n".join(lines).strip(), failing_layer


def _build_repair_prompt(
    *,
    schema: str,
    policy_spec: str,
    previous_candidate: str,
    failure_feedback: str,
    failing_layer: str,
    iteration: int,
    oscillation_warning: str = "",
) -> str:
    template_name = {
        "syntax": "repair_syntax",
        "schema": "repair_schema",
        "semantic": "repair_semantic",
    }.get(failing_layer, "repair_semantic")
    template = _load_prompt_template(template_name)
    assets = _load_assets()
    return template.format(
        ITERATION=iteration,
        POLICY_SPEC=policy_spec,
        CEDAR_SCHEMA=schema,
        PREVIOUS_CANDIDATE=previous_candidate,
        FAILURE_FEEDBACK=failure_feedback,
        CEDAR_SYNTAX_CHEAT_SHEET=assets["cheat_sheet"],
        OSCILLATION_WARNING=oscillation_warning,
    )


def run_once(
    task_id: str,
    task_path: Path,
    variant: str,
    model: str,
    base_url: str,
    temperature: float,
    max_tokens: int,
    run_root: Path,
    keep_eval_workspace: bool,
) -> RunRecord:
    schema, policy_spec = _load_task_inputs(task_path)
    assets = _load_assets()
    prompt = _build_prompt(variant, schema, policy_spec, assets)

    run_dir = run_root / f"{task_id}_{variant}"
    _copy_task_workspace(task_path, run_dir)
    log_path = run_dir / "run.log"
    log_lines: list[str] = []

    _print_and_log(log_lines, "=" * 72)
    _print_and_log(log_lines, f"RUN START")
    _print_and_log(log_lines, f"task:     {task_id}")
    _print_and_log(log_lines, f"strategy: {variant}")
    _print_and_log(log_lines, f"model:    {model}")
    _print_and_log(log_lines, f"base_url: {base_url}")
    _print_and_log(log_lines, "=" * 72)
    _print_and_log(log_lines, "")
    _print_and_log(log_lines, "--- Prompt ---")
    _print_and_log(log_lines, prompt)

    t0 = time.monotonic()
    raw_output = _call_model(base_url, model, prompt, temperature, max_tokens)
    candidate = _extract_cedar(raw_output)

    raw_output_path = run_dir / "raw_model_output.txt"
    candidate_path = run_dir / "candidate.cedar"
    prompt_path = run_dir / "prompt.txt"

    raw_output_path.write_text(raw_output)
    candidate_path.write_text(candidate)
    prompt_path.write_text(prompt)

    _print_and_log(log_lines, "")
    _print_and_log(log_lines, "--- Raw Model Output ---")
    _print_and_log(log_lines, raw_output)
    _print_and_log(log_lines, "")
    _print_and_log(log_lines, "--- Extracted Candidate ---")
    _print_and_log(log_lines, candidate)

    eval_workspace = _prepare_eval_workspace(
        task_path=task_path,
        eval_workspace=run_dir / "_eval_workspace",
        candidate_text=candidate,
    )

    bundle = evaluate_workspace(eval_workspace, prompt_variant=variant)
    duration_s = round(time.monotonic() - t0, 3)

    verification_path = run_dir / "verification_result.json"
    verification_path.write_text(json.dumps(bundle.verification, indent=2))
    (run_dir / "evaluation_bundle.json").write_text(json.dumps(bundle.__dict__, indent=2))

    _print_and_log(log_lines, "")
    _print_and_log(log_lines, "--- Evaluation ---")
    for stage in bundle.stages:
        _print_and_log(log_lines, f"[{stage['name'].upper()}]")
        _print_and_log(
            log_lines,
            f"status={stage['status']} passed={stage['passed']}",
        )
        _print_and_log(log_lines, f"message: {stage['message']}")
        details = stage.get("details", {})
        if stage["name"] == "semantic" and details.get("checks"):
            _print_and_log(log_lines, f"total_checks: {details.get('total_checks', 0)}")
            if "solver_time_s" in details:
                _print_and_log(log_lines, f"solver_time_s: {details['solver_time_s']}")
            _print_and_log(log_lines, "")
            _print_and_log(log_lines, "semantic check results:")
            for check in details["checks"]:
                status = "PASS" if check["passed"] else "FAIL"
                _print_and_log(
                    log_lines,
                    f"  - {check['name']} [{check['type']}] {status}",
                )
                _print_and_log(log_lines, f"    description: {check['description']}")
                if not check["passed"] and check.get("counterexample"):
                    _print_and_log(log_lines, "    counterexample:")
                    _print_and_log(log_lines, _shorten(check["counterexample"], 700))
            other_details = {k: v for k, v in details.items() if k != "checks"}
            if other_details.get("failed_checks"):
                _print_and_log(log_lines, f"failed_checks: {', '.join(other_details['failed_checks'])}")
        elif details:
            explanation = details.get("explanation")
            if explanation:
                _print_and_log(log_lines, "explanation:")
                _print_and_log(log_lines, f"  summary: {explanation.get('summary', '')}")
                _print_and_log(log_lines, f"  likely_cause: {explanation.get('likely_cause', '')}")
                _print_and_log(log_lines, f"  suggested_fix: {explanation.get('suggested_fix', '')}")
            if details.get("error"):
                _print_and_log(log_lines, "raw_error:")
                _print_and_log(log_lines, _shorten(details["error"], 1200))
            remaining = {
                k: v for k, v in details.items()
                if k not in {"explanation", "error"}
            }
            if remaining:
                _print_and_log(log_lines, json.dumps(remaining, indent=2))
        _print_and_log(log_lines, "")

    _print_and_log(log_lines, "--- Metrics ---")
    _print_and_log(log_lines, f"SyntaxPass:        {bundle.syntax_pass}")
    _print_and_log(log_lines, f"SchemaPass:        {bundle.schema_pass}")
    _print_and_log(log_lines, f"SemanticAccuracy:  {bundle.semantic_accuracy}")
    _print_and_log(log_lines, f"VerificationPass:  {bundle.verification_pass}")
    _print_and_log(log_lines, f"Loss:              {bundle.loss}")
    if bundle.failed_checks:
        _print_and_log(log_lines, f"FailedChecks:      {', '.join(bundle.failed_checks)}")
    _print_and_log(log_lines, f"DurationSec:       {duration_s}")
    _print_and_log(log_lines, "")
    _print_and_log(log_lines, f"log saved to: {log_path}")
    log_path.write_text("\n".join(log_lines) + "\n")

    if not keep_eval_workspace and eval_workspace.exists():
        shutil.rmtree(eval_workspace)

    return RunRecord(
        run_id=run_root.name,
        task_id=task_id,
        task_path=str(task_path),
        prompt_variant=variant,
        model=model,
        base_url=base_url,
        syntax_pass=bundle.syntax_pass,
        verification_pass=bundle.verification_pass,
        loss=bundle.loss,
        failed_checks=bundle.failed_checks,
        failed_check_types=bundle.failed_check_types,
        duration_s=duration_s,
        metrics=bundle.metrics,
        raw_output_path=str(raw_output_path),
        candidate_path=str(candidate_path),
        workspace_path=str(eval_workspace),
        log_path=str(log_path),
    )


OSCILLATION_THRESHOLD = 3


def run_repair_loop(
    task_id: str,
    task_path: Path,
    variant: str,
    model: str,
    base_url: str,
    temperature: float,
    max_tokens: int,
    run_root: Path,
    keep_eval_workspace: bool,
    max_iterations: int,
) -> dict:
    schema, policy_spec = _load_task_inputs(task_path)
    assets = _load_assets()
    initial_prompt = _build_prompt(variant, schema, policy_spec, assets)

    iteration_records: list[IterationRecord] = []
    bundle = None
    candidate_text = ""
    stop_reason = "max_iterations_reached"

    # v2 state tracking
    candidate_hashes: list[str] = []
    failure_layer_sequence: list[str] = []
    best_candidate = ""
    best_loss: float = float("inf")
    best_candidate_iteration: int | None = None
    oscillation_count = 0

    for iteration in range(1, max_iterations + 1):
        if iteration == 1:
            prompt = initial_prompt
            prompt_variant = variant
        else:
            oscillation_warning = ""
            if _is_oscillating(candidate_hashes, failure_layer_sequence):
                oscillation_count += 1
                oscillation_warning = (
                    f"WARNING: Oscillation detected (#{oscillation_count}). "
                    "You have been alternating between error types without converging.\n"
                    "Rules for this attempt:\n"
                    "1. Ensure syntax is correct FIRST — do not change policy logic while fixing syntax.\n"
                    "2. Once syntax passes, address semantic issues separately.\n"
                    "3. Do not revert to a candidate that failed syntax."
                )
                repair_base = best_candidate if best_candidate else candidate_text
            else:
                repair_base = candidate_text

            failure_feedback, failing_layer = _render_failure_feedback(bundle, task_path)
            prompt = _build_repair_prompt(
                schema=schema,
                policy_spec=policy_spec,
                previous_candidate=repair_base,
                failure_feedback=failure_feedback,
                failing_layer=failing_layer,
                iteration=iteration,
                oscillation_warning=oscillation_warning,
            )
            prompt_variant = f"{variant}_repair_{failing_layer}"

        iteration_dir = run_root / f"{task_id}_iter_{iteration:02d}"
        if iteration_dir.exists():
            shutil.rmtree(iteration_dir)
        iteration_dir.mkdir(parents=True, exist_ok=True)

        log_path = iteration_dir / "run.log"
        log_lines: list[str] = []

        _print_and_log(log_lines, "=" * 72)
        _print_and_log(log_lines, "ITERATION START")
        _print_and_log(log_lines, f"task:       {task_id}")
        _print_and_log(log_lines, f"iteration:  {iteration}")
        _print_and_log(log_lines, f"strategy:   {prompt_variant}")
        _print_and_log(log_lines, f"model:      {model}")
        _print_and_log(log_lines, f"base_url:   {base_url}")
        _print_and_log(log_lines, "=" * 72)
        _print_and_log(log_lines, "")
        _print_and_log(log_lines, "--- Prompt ---")
        _print_and_log(log_lines, prompt)

        iter_temperature = temperature if iteration == 1 else REPAIR_TEMPERATURE
        _print_and_log(log_lines, f"temperature: {iter_temperature}")
        t0 = time.monotonic()
        raw_output = _call_model(base_url, model, prompt, iter_temperature, max_tokens)
        candidate = _extract_cedar(raw_output)
        duration_s = round(time.monotonic() - t0, 3)

        raw_output_path = iteration_dir / "raw_model_output.txt"
        candidate_path = iteration_dir / "candidate.cedar"
        prompt_path = iteration_dir / "prompt.txt"
        raw_output_path.write_text(raw_output)
        candidate_path.write_text(candidate)
        prompt_path.write_text(prompt)

        _print_and_log(log_lines, "")
        _print_and_log(log_lines, "--- Raw Model Output ---")
        _print_and_log(log_lines, raw_output)
        _print_and_log(log_lines, "")
        _print_and_log(log_lines, "--- Extracted Candidate ---")
        _print_and_log(log_lines, candidate)

        eval_workspace = _prepare_eval_workspace(
            task_path=task_path,
            eval_workspace=iteration_dir / "_eval_workspace",
            candidate_text=candidate,
        )
        bundle = evaluate_workspace(eval_workspace, prompt_variant=prompt_variant)

        verification_path = iteration_dir / "verification_result.json"
        bundle_path = iteration_dir / "evaluation_bundle.json"
        verification_path.write_text(json.dumps(bundle.verification, indent=2))
        bundle_path.write_text(json.dumps(bundle.__dict__, indent=2))

        _print_and_log(log_lines, "")
        _print_and_log(log_lines, "--- Evaluation ---")
        for stage in bundle.stages:
            _print_and_log(log_lines, f"[{stage['name'].upper()}]")
            _print_and_log(log_lines, f"status={stage['status']} passed={stage['passed']}")
            _print_and_log(log_lines, f"message: {stage['message']}")
            details = stage.get("details", {})
            if stage["name"] == "semantic" and details.get("checks"):
                _print_and_log(log_lines, f"total_checks: {details.get('total_checks', 0)}")
                if "solver_time_s" in details:
                    _print_and_log(log_lines, f"solver_time_s: {details['solver_time_s']}")
                _print_and_log(log_lines, "")
                _print_and_log(log_lines, "semantic check results:")
                for check in details["checks"]:
                    status = "PASS" if check["passed"] else "FAIL"
                    _print_and_log(
                        log_lines,
                        f"  - {check['name']} [{check['type']}] {status}",
                    )
                    _print_and_log(log_lines, f"    description: {check['description']}")
                    if not check["passed"] and check.get("counterexample"):
                        _print_and_log(log_lines, "    counterexample:")
                        _print_and_log(log_lines, _shorten(check["counterexample"], 700))
            elif details:
                explanation = details.get("explanation")
                if explanation:
                    _print_and_log(log_lines, "explanation:")
                    _print_and_log(log_lines, f"  summary: {explanation.get('summary', '')}")
                    _print_and_log(log_lines, f"  likely_cause: {explanation.get('likely_cause', '')}")
                    _print_and_log(log_lines, f"  suggested_fix: {explanation.get('suggested_fix', '')}")
                if details.get("error"):
                    _print_and_log(log_lines, "raw_error:")
                    _print_and_log(log_lines, _shorten(details["error"], 1200))
            _print_and_log(log_lines, "")

        _print_and_log(log_lines, "--- Metrics ---")
        _print_and_log(log_lines, f"SyntaxPass:        {bundle.syntax_pass}")
        _print_and_log(log_lines, f"SchemaPass:        {bundle.schema_pass}")
        _print_and_log(log_lines, f"SemanticAccuracy:  {bundle.semantic_accuracy}")
        _print_and_log(log_lines, f"VerificationPass:  {bundle.verification_pass}")
        _print_and_log(log_lines, f"Loss:              {bundle.loss}")
        if bundle.failed_checks:
            _print_and_log(log_lines, f"FailedChecks:      {', '.join(bundle.failed_checks)}")
        _print_and_log(log_lines, f"DurationSec:       {duration_s}")
        _print_and_log(log_lines, "")
        _print_and_log(log_lines, f"log saved to: {log_path}")
        log_path.write_text("\n".join(log_lines) + "\n")

        iteration_records.append(
            IterationRecord(
                iteration=iteration,
                is_repair_iteration=(iteration > 1),
                prompt_variant=prompt_variant,
                syntax_pass=bundle.syntax_pass,
                schema_pass=bundle.schema_pass,
                semantic_accuracy=bundle.semantic_accuracy,
                verification_pass=bundle.verification_pass,
                loss=bundle.loss,
                failed_checks=bundle.failed_checks,
                failed_check_types=bundle.failed_check_types,
                duration_s=duration_s,
                metrics=bundle.metrics,
                raw_output_path=str(raw_output_path),
                candidate_path=str(candidate_path),
                evaluation_bundle_path=str(bundle_path),
                verification_result_path=str(verification_path),
                workspace_path=str(eval_workspace),
                prompt_path=str(prompt_path),
                log_path=str(log_path),
            )
        )

        candidate_text = candidate

        # Track candidate hash and failing layer for oscillation detection
        candidate_hashes.append(hashlib.sha256(candidate.encode()).hexdigest())
        if not bundle.syntax_pass:
            flayer = "syntax"
        elif not bundle.schema_pass:
            flayer = "schema"
        elif not bundle.verification_pass:
            flayer = "semantic"
        else:
            flayer = "pass"
        failure_layer_sequence.append(flayer)

        # Track best candidate (syntax-passing, lowest loss)
        if bundle.syntax_pass and bundle.loss < best_loss:
            best_loss = bundle.loss
            best_candidate = candidate
            best_candidate_iteration = iteration

        print(
            f"[iteration={iteration}] syntax_pass={bundle.syntax_pass} "
            f"schema_pass={bundle.schema_pass} verification_pass={bundle.verification_pass} "
            f"semantic_accuracy={bundle.semantic_accuracy} loss={bundle.loss} "
            f"layer={flayer} oscillation_count={oscillation_count}"
        )

        if not keep_eval_workspace and eval_workspace.exists():
            shutil.rmtree(eval_workspace)

        if bundle.verification_pass:
            stop_reason = "verification_pass"
            break

        if oscillation_count >= OSCILLATION_THRESHOLD:
            stop_reason = "oscillation_no_progress"
            break

    final_record = iteration_records[-1]
    first_success_iteration = next(
        (record.iteration for record in iteration_records if record.verification_pass),
        None,
    )
    best_semantic_accuracy = max(record.semantic_accuracy for record in iteration_records)

    loop_record = RepairLoopRecord(
        run_id=run_root.name,
        task_id=task_id,
        task_path=str(task_path),
        initial_prompt_variant=variant,
        model=model,
        base_url=base_url,
        max_iterations=max_iterations,
        completed_iterations=len(iteration_records),
        stop_reason=stop_reason,
        final_syntax_pass=final_record.syntax_pass,
        final_schema_pass=final_record.schema_pass,
        final_semantic_accuracy=final_record.semantic_accuracy,
        final_verification_pass=final_record.verification_pass,
        final_loss=final_record.loss,
        best_semantic_accuracy=best_semantic_accuracy,
        best_candidate_iteration=best_candidate_iteration,
        first_success_iteration=first_success_iteration,
        oscillation_count=oscillation_count,
        failure_layer_sequence=failure_layer_sequence,
        iterations=[asdict(record) for record in iteration_records],
    )

    summary = {
        "mode": "repair",
        "run_id": run_root.name,
        "task_id": task_id,
        "task_path": str(task_path),
        "model": model,
        "base_url": base_url,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "max_iterations": max_iterations,
        "stop_reason": stop_reason,
        "completed_iterations": len(iteration_records),
        "final_verification_pass": final_record.verification_pass,
        "best_semantic_accuracy": best_semantic_accuracy,
        "first_success_iteration": first_success_iteration,
        "results": [asdict(record) for record in iteration_records],
        "metrics_by_prompt_variant": [
            strategy_summary_to_dict(summary)
            for summary in aggregate_by_prompt_variant(
                [RunMetricRecord(**record.metrics) for record in iteration_records]
            )
        ],
        "metrics_by_iteration": [
            {
                "iteration": record.iteration,
                "syntax_pass": record.syntax_pass,
                "schema_pass": record.schema_pass,
                "semantic_accuracy": record.semantic_accuracy,
                "verification_pass": record.verification_pass,
                "loss": record.loss,
            }
            for record in iteration_records
        ],
        "repair_loop_record": asdict(loop_record),
    }
    (run_root / "summary.json").write_text(json.dumps(summary, indent=2))
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run CedarForge single-model baseline experiments")
    parser.add_argument("--task", required=True, help="Task id from tasks.json")
    parser.add_argument("--mode", choices=["single", "repair"], default="single", help="Run a single baseline pass or a verifier-guided repair loop")
    parser.add_argument("--variant", choices=PROMPT_VARIANTS, help="Single prompt variant to run")
    parser.add_argument("--all-variants", action="store_true", help="Run all prompt variants")
    parser.add_argument("--model", required=True, help="OpenAI-compatible model id")
    parser.add_argument("--base-url", required=True, help="OpenAI-compatible base URL")
    parser.add_argument("--temperature", type=float, default=0.0, help="Sampling temperature")
    parser.add_argument("--max-tokens", type=int, default=2048, help="Max completion tokens")
    parser.add_argument("--max-iterations", type=int, default=3, help="Maximum total iterations for repair mode, including the first generation")
    parser.add_argument("--run-id", default=None, help="Optional run id")
    parser.add_argument(
        "--keep-eval-workspace",
        action="store_true",
        help="Keep the temporary internal evaluation workspace in the run directory",
    )
    args = parser.parse_args()

    if args.mode == "single":
        if not args.variant and not args.all_variants:
            parser.error("Specify --variant or --all-variants")
    else:
        if args.all_variants:
            parser.error("--all-variants is not supported in repair mode")
        if not args.variant:
            parser.error("Specify --variant in repair mode")
        if args.max_iterations < 1:
            parser.error("--max-iterations must be at least 1")

    registry = _load_task_registry()
    if args.task not in registry:
        raise SystemExit(f"Unknown task id: {args.task}")

    task_entry = registry[args.task]
    task_path = _task_abs_path(task_entry["path"])
    if not task_path.exists():
        raise SystemExit(f"Task path does not exist: {task_path}")

    run_id = args.run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    if args.mode == "repair":
        run_root = RUNS_DIR / f"{run_id}_repair_loop"
        run_root.mkdir(parents=True, exist_ok=True)
        run_repair_loop(
            task_id=args.task,
            task_path=task_path,
            variant=args.variant,
            model=args.model,
            base_url=args.base_url,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            run_root=run_root,
            keep_eval_workspace=args.keep_eval_workspace,
            max_iterations=args.max_iterations,
        )
        return 0

    variants = PROMPT_VARIANTS if args.all_variants else [args.variant]
    run_root = RUNS_DIR / run_id
    run_root.mkdir(parents=True, exist_ok=True)

    results = []
    for variant in variants:
        record = run_once(
            task_id=args.task,
            task_path=task_path,
            variant=variant,
            model=args.model,
            base_url=args.base_url,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            run_root=run_root,
            keep_eval_workspace=args.keep_eval_workspace,
        )
        results.append(asdict(record))
        print(
            f"[{variant}] syntax_pass={record.syntax_pass} "
            f"verification_pass={record.verification_pass} loss={record.loss} "
            f"duration={record.duration_s}s"
        )

    aggregated_metrics = aggregate_by_prompt_variant(
        [RunMetricRecord(**r["metrics"]) for r in results]
    )

    summary = {
        "mode": "single",
        "run_id": run_id,
        "task_id": args.task,
        "task_path": str(task_path),
        "model": args.model,
        "base_url": args.base_url,
        "temperature": args.temperature,
        "max_tokens": args.max_tokens,
        "results": results,
        "metrics_by_prompt_variant": [strategy_summary_to_dict(s) for s in aggregated_metrics],
    }
    (run_root / "summary.json").write_text(json.dumps(summary, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
