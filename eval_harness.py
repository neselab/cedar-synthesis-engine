"""
Cedar Synthesis Engine — Evaluation Harness

Runs the full two-phase synthesis pipeline (Decidable CEGIS) across scenarios:
  Phase 1: Generate verification plan + reference policies from NL spec
  Phase 2: CEGIS loop — synthesize candidate → verify → fix from counterexamples

Logs per-iteration metrics (loss, solver time, counterexample count) and
aggregates results across scenarios and models.

By default, a human-in-the-loop review gate runs between Phase 1 and Phase 2:
the harness presents each reference policy with a plain-language summary and
waits for approval.  Pass --no-review for fully automated benchmark runs.

Usage:
    # Single pre-configured scenario (verification plan already exists)
    python eval_harness.py --scenario experiments/github

    # Force Phase 1 regeneration
    python eval_harness.py --scenario experiments/github --gen-references

    # Multiple scenarios with a specific model
    python eval_harness.py --scenario experiments/github workspace --model claude-sonnet-4-20250514

    # All discovered scenarios
    python eval_harness.py --all --max-iters 20

    # Fully automated (skip human review)
    python eval_harness.py --scenario experiments/github --no-review

    # Compare models (automated)
    python eval_harness.py --all --no-review --model claude-sonnet-4-20250514 claude-haiku-4-5-20251001
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from anthropic import Anthropic

from orchestrator import load_checks, run_verification
from solver_wrapper import CheckResult, VerificationResult

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
EVAL_RUNS_DIR = os.path.join(ROOT_DIR, "eval_runs")

DEFAULT_MODEL = "claude-sonnet-4-20250514"
MAX_ITERATIONS = 20


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class IterationLog:
    iteration: int
    loss: int
    checks_passed: int
    checks_total: int
    solver_time_s: float
    counterexample_count: int
    syntax_valid: bool
    status: str             # "pass", "fail", "syntax_error", "llm_error"


@dataclass
class ScenarioResult:
    scenario: str
    model: str
    converged: bool
    iterations: int
    max_iterations: int
    total_time_s: float
    phase1_time_s: float
    phase2_time_s: float
    final_loss: int
    checks_total: int
    iteration_log: list     # list[dict] (serialized IterationLog)
    error: str = ""


# ---------------------------------------------------------------------------
# Phase 1: Reference Generation
# ---------------------------------------------------------------------------

PHASE1_SYSTEM = """\
You are an expert in Cedar access control policies and formal verification.
Given a Cedar schema and a natural-language policy specification, generate a
verification plan: a set of formal checks with reference Cedar policies that
bound the correct behavior.

Output ONLY valid JSON with this exact structure:
{
  "checks": [
    {
      "name": "short_snake_case_name",
      "description": "Human-readable description of what this check verifies",
      "type": "implies | floor | always-denies-liveness",
      "principal_type": "EntityType",
      "action": "Action::\\"actionName\\"",
      "resource_type": "EntityType",
      "reference_file": "ceiling_action.cedar or floor_action.cedar"
    }
  ],
  "references": {
    "ceiling_action.cedar": "permit (\\n    principal is User,\\n    ...\\n);",
    "floor_action.cedar": "permit (...);"
  }
}

Rules:
- Safety requirements → "implies" checks with ceiling reference policies.
  The ceiling defines the MAXIMUM allowed behavior. Check: candidate ≤ ceiling.
- Minimum-access requirements → "floor" checks with floor reference policies.
  The floor defines the MINIMUM that MUST be allowed. Check: floor ≤ candidate.
- Liveness requirements → "always-denies-liveness" checks (no reference file needed).
  Verifies the policy doesn't trivially deny all requests for that action.
- Reference policies must be valid Cedar syntax against the provided schema.
- Use exact entity types, actions, and attribute names from the schema.
- For "always-denies-liveness" checks, omit the "reference_file" field.
- Each reference file should contain exactly one permit or forbid statement."""


def _extract_json(text: str) -> dict:
    """Extract JSON from an LLM response that may contain markdown fencing."""
    # Try ```json ... ``` blocks first
    m = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if m:
        return json.loads(m.group(1))
    # Try raw JSON object
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        return json.loads(m.group(0))
    raise ValueError("No JSON found in LLM response")


def generate_references(
    client: Anthropic,
    model: str,
    schema: str,
    policy_spec: str,
    example_plan: str = "",
    feedback: str = "",
    previous_plan: dict | None = None,
) -> dict:
    """
    Phase 1: LLM generates verification plan + reference policies.

    If *feedback* and *previous_plan* are provided, the LLM is asked to
    revise the previous plan according to the human reviewer's feedback
    rather than generating from scratch.
    """
    prompt = f"""Generate a verification plan and reference policies for this scenario.

## Cedar Schema
```
{schema}
```

## Policy Specification
{policy_spec}
"""
    if example_plan and not previous_plan:
        prompt += f"""
## Example (another scenario — use for format reference only)
```python
{example_plan}
```
"""
    if feedback:
        if previous_plan:
            prompt += f"""
## Previous Plan (rejected by reviewer)
```json
{json.dumps(previous_plan, indent=2)}
```
"""
        prompt += f"""
## Reviewer Feedback
{feedback}

Revise the verification plan and reference policies to address the feedback above.
"""
    response = client.messages.create(
        model=model,
        max_tokens=8192,
        system=PHASE1_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return _extract_json(response.content[0].text)


def write_phase1_artifacts(workspace: str, plan_data: dict) -> None:
    """Write verification_plan.py and reference policies from Phase 1 JSON."""
    refs_dir = os.path.join(workspace, "references")
    os.makedirs(refs_dir, exist_ok=True)

    # Write reference Cedar files
    for filename, content in plan_data.get("references", {}).items():
        with open(os.path.join(refs_dir, filename), "w") as f:
            f.write(content)

    # Generate verification_plan.py
    lines = [
        '"""Auto-generated verification plan."""',
        "import os",
        "",
        'REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")',
        "",
        "",
        "def get_checks():",
        "    return [",
    ]

    for check in plan_data["checks"]:
        lines.append("        {")
        lines.append(f'            "name": {json.dumps(check["name"])},')
        lines.append(f'            "description": {json.dumps(check["description"])},')
        lines.append(f'            "type": {json.dumps(check["type"])},')
        lines.append(f'            "principal_type": {json.dumps(check["principal_type"])},')
        lines.append(f'            "action": {json.dumps(check["action"])},')
        lines.append(f'            "resource_type": {json.dumps(check["resource_type"])},')

        ref_file = check.get("reference_file")
        if check["type"] == "implies" and ref_file:
            lines.append(f'            "reference_path": os.path.join(REFS, {json.dumps(ref_file)}),')
        elif check["type"] == "floor" and ref_file:
            lines.append(f'            "floor_path": os.path.join(REFS, {json.dumps(ref_file)}),')

        lines.append("        },")

    lines.append("    ]")
    lines.append("")

    with open(os.path.join(workspace, "verification_plan.py"), "w") as f:
        f.write("\n".join(lines))


# ---------------------------------------------------------------------------
# Phase 1.5: Human-in-the-loop Reference Review
# ---------------------------------------------------------------------------

def review_references(workspace: str, schema: str) -> tuple[bool, str]:
    """
    Interactive review of verification plan + reference policies.

    Presents each reference policy with its raw Cedar code and a
    plain-language NL summary (via translator.policy_to_nl), following
    the same presentation pattern as review.py.

    Returns:
        (True, "")           — human approved
        (False, feedback)    — human rejected with feedback for regeneration
        (False, "SKIP")      — human chose to skip this scenario
    """
    checks = load_checks(workspace)
    refs_dir = os.path.join(workspace, "references")

    # ── Show verification plan overview ──
    print(f"\n{'=' * 60}")
    print("  REFERENCE POLICY REVIEW")
    print(f"{'=' * 60}")

    print(f"\n  Verification Plan: {len(checks)} check(s)\n")
    for c in checks:
        tag = ""
        if c["type"] == "implies":
            tag = os.path.basename(c.get("reference_path", ""))
        elif c["type"] == "floor":
            tag = os.path.basename(c.get("floor_path", ""))
        suffix = f"  [{tag}]" if tag else ""
        print(f"    {c['name']} ({c['type']}){suffix}")
        print(f"      {c['description']}")

    # ── Show each reference policy ──
    ref_files = (
        sorted(f for f in os.listdir(refs_dir) if f.endswith(".cedar"))
        if os.path.isdir(refs_dir)
        else []
    )

    # Try to import NL translator (optional — graceful degradation)
    _policy_to_nl = None
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            from translator import policy_to_nl
            _policy_to_nl = policy_to_nl
        except ImportError:
            pass

    for ref_file in ref_files:
        ref_path = os.path.join(refs_dir, ref_file)
        with open(ref_path) as f:
            policy_text = f.read()

        if ref_file.startswith("ceiling_"):
            policy_type = "CEILING (maximum permissive boundary)"
        elif ref_file.startswith("floor_"):
            policy_type = "FLOOR (minimum required access)"
        else:
            policy_type = "REFERENCE"

        print(f"\n  {'─' * 56}")
        print(f"    {ref_file}")
        print(f"    Type: {policy_type}")
        print(f"  {'─' * 56}")

        print(f"\n    Cedar policy:")
        for line in policy_text.strip().split("\n"):
            print(f"      {line}")

        if _policy_to_nl:
            try:
                nl = _policy_to_nl(policy_text, schema)
                print(f"\n    Plain language summary:")
                for line in nl.strip().split("\n"):
                    print(f"      {line}")
            except Exception as e:
                print(f"\n    (NL summary unavailable: {e})")
        else:
            print(f"\n    (NL summary unavailable — set ANTHROPIC_API_KEY)")

    # ── Approval prompt ──
    print(f"\n  {'─' * 56}")
    print("  Options:")
    print("    [Enter]      Approve all references and proceed to synthesis")
    print("    [feedback]   Reject — type feedback for the LLM to regenerate")
    print("    [q]          Skip this scenario")

    try:
        response = input("\n  > ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\n  Skipped.")
        return False, "SKIP"

    if not response:
        print("  Approved.")
        return True, ""
    elif response.lower() == "q":
        return False, "SKIP"
    else:
        return False, response


# ---------------------------------------------------------------------------
# Phase 2: CEGIS Synthesis Loop
# ---------------------------------------------------------------------------

PHASE2_SYSTEM = """\
You are an expert Cedar policy synthesizer. Your goal is to write a Cedar
policy that passes ALL formal verification checks.

Rules:
- Output ONLY the Cedar policy code — no markdown fencing, no explanations.
- The policy must be valid Cedar syntax against the provided schema.
- Use counterexamples from failed checks to diagnose and fix violations.
- Cedar denies by default — you only need permit and forbid rules.
- `forbid` always overrides `permit` in Cedar.
- Use `unless` clauses for exceptions to forbid rules.

Cedar quick reference:
  permit (principal, action == Action::"act", resource) when { conditions };
  forbid (principal, action == Action::"act", resource) when { cond } unless { exceptions };
  principal in Group::"name"    // group membership
  principal.attr == "value"     // attribute access
  context.field                 // request context"""


def _strip_cedar_fencing(text: str) -> str:
    """Remove markdown code fencing from LLM output."""
    text = text.strip()
    text = re.sub(r"^```(?:cedar)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    return text.strip()


def _format_initial_prompt(schema: str, policy_spec: str, checks: list[dict]) -> str:
    """Build the first user message for the synthesis conversation."""
    parts = [
        f"## Cedar Schema\n```\n{schema}\n```\n",
        f"## Policy Specification\n{policy_spec}\n",
        "## Verification Checks\nYour policy must pass ALL of these:\n",
    ]
    for c in checks:
        parts.append(f"- **{c['name']}** ({c['type']}): {c['description']}")
    parts.append(
        "\nWrite a Cedar policy that satisfies every check. Output ONLY Cedar code."
    )
    return "\n".join(parts)


def _format_feedback(vr: VerificationResult) -> str:
    """Build a feedback message from verification results."""
    parts = [f"## Verification Results — {vr.loss} check(s) FAILED\n"]
    for r in vr.results:
        mark = "PASS" if r.passed else "FAIL"
        parts.append(f"- {r.check_name} ({r.check_type}): **{mark}**")
        if not r.passed and r.counterexample:
            parts.append(f"  Counterexample:\n  ```\n  {r.counterexample}\n  ```")
    parts.append(
        "\nFix the policy to address every failure. Output the COMPLETE updated policy."
    )
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Scenario setup
# ---------------------------------------------------------------------------

def setup_workspace(scenario_path: str, run_dir: str) -> str:
    """Copy scenario files into an isolated eval workspace. Returns workspace path."""
    scenario_name = os.path.basename(os.path.normpath(scenario_path))
    workspace = os.path.join(run_dir, scenario_name)
    os.makedirs(workspace, exist_ok=True)

    # Copy schema (experiments use schema.cedarschema, dataset uses policies.cedarschema)
    for name in ("schema.cedarschema", "policies.cedarschema"):
        src = os.path.join(scenario_path, name)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(workspace, "schema.cedarschema"))
            break

    # Copy policy spec
    spec_src = os.path.join(scenario_path, "policy_spec.md")
    if os.path.exists(spec_src):
        shutil.copy2(spec_src, os.path.join(workspace, "policy_spec.md"))

    # Copy existing verification plan + references
    vp_src = os.path.join(scenario_path, "verification_plan.py")
    if os.path.exists(vp_src):
        shutil.copy2(vp_src, os.path.join(workspace, "verification_plan.py"))

    refs_src = os.path.join(scenario_path, "references")
    if os.path.isdir(refs_src):
        refs_dst = os.path.join(workspace, "references")
        if os.path.exists(refs_dst):
            shutil.rmtree(refs_dst)
        shutil.copytree(refs_src, refs_dst)

    # Seed empty policy store
    store_path = os.path.join(workspace, "policy_store.cedar")
    if not os.path.exists(store_path):
        with open(store_path, "w") as f:
            f.write("// Policy store — verified policies appended here\n")

    return workspace


def _load_plan_data_from_workspace(workspace: str) -> dict:
    """Reconstruct a plan_data dict from existing workspace files on disk."""
    checks_raw = load_checks(workspace)
    refs_dir = os.path.join(workspace, "references")

    # Build check list in the same JSON shape that generate_references produces
    checks = []
    for c in checks_raw:
        entry = {
            "name": c["name"],
            "description": c["description"],
            "type": c["type"],
            "principal_type": c["principal_type"],
            "action": c["action"],
            "resource_type": c["resource_type"],
        }
        if c["type"] == "implies":
            entry["reference_file"] = os.path.basename(c.get("reference_path", ""))
        elif c["type"] == "floor":
            entry["reference_file"] = os.path.basename(c.get("floor_path", ""))
        checks.append(entry)

    # Read reference Cedar files
    references = {}
    if os.path.isdir(refs_dir):
        for fname in sorted(os.listdir(refs_dir)):
            if fname.endswith(".cedar"):
                with open(os.path.join(refs_dir, fname)) as f:
                    references[fname] = f.read()

    return {"checks": checks, "references": references}


# ---------------------------------------------------------------------------
# Scenario runner
# ---------------------------------------------------------------------------

def run_scenario(
    scenario_path: str,
    run_dir: str,
    model: str,
    max_iters: int,
    gen_references: bool,
    no_review: bool = False,
) -> ScenarioResult:
    """Run the full two-phase evaluation for a single scenario."""
    scenario_name = os.path.basename(os.path.normpath(scenario_path))
    scenario_path = os.path.abspath(scenario_path)
    t_start = time.monotonic()

    print(f"\n{'=' * 60}")
    print(f"SCENARIO: {scenario_name}")
    print(f"Model:    {model}")
    print(f"{'=' * 60}")

    def _err(msg: str, **kw) -> ScenarioResult:
        return ScenarioResult(
            scenario=scenario_name, model=model, converged=False,
            iterations=0, max_iterations=max_iters,
            total_time_s=round(time.monotonic() - t_start, 2),
            phase1_time_s=kw.get("p1", 0.0), phase2_time_s=0.0,
            final_loss=-1, checks_total=0, iteration_log=[], error=msg,
        )

    # Setup workspace
    workspace = setup_workspace(scenario_path, run_dir)
    schema_path = os.path.join(workspace, "schema.cedarschema")

    if not os.path.exists(schema_path):
        return _err("No schema found")

    with open(schema_path) as f:
        schema = f.read()

    spec_path = os.path.join(workspace, "policy_spec.md")
    policy_spec = ""
    if os.path.exists(spec_path):
        with open(spec_path) as f:
            policy_spec = f.read()

    client = Anthropic()

    # ── Phase 1: Reference Generation ─────────────────────────────────────
    phase1_time = 0.0
    vp_exists = os.path.exists(os.path.join(workspace, "verification_plan.py"))
    phase1_ran = False
    plan_data = None

    if gen_references or not vp_exists:
        if not policy_spec:
            return _err(
                "No policy_spec.md and no verification_plan.py — "
                "cannot run Phase 1 without a spec"
            )

        print("\n--- Phase 1: Generating verification plan + references ---")
        t1 = time.monotonic()

        # Load example for few-shot context
        example_plan = ""
        example_vp = os.path.join(ROOT_DIR, "experiments", "github", "verification_plan.py")
        if os.path.exists(example_vp):
            with open(example_vp) as f:
                example_plan = f.read()

        try:
            plan_data = generate_references(client, model, schema, policy_spec, example_plan)
            write_phase1_artifacts(workspace, plan_data)
            phase1_time = time.monotonic() - t1
            phase1_ran = True
            n_checks = len(plan_data["checks"])
            n_refs = len(plan_data.get("references", {}))
            print(f"  Generated {n_checks} checks, {n_refs} reference policies ({phase1_time:.1f}s)")
        except Exception as e:
            phase1_time = time.monotonic() - t1
            return _err(f"Phase 1 failed: {e}", p1=round(phase1_time, 2))
    else:
        print("\n--- Phase 1: Using existing verification plan ---")

    # ── Phase 1.5: Human Review Gate ──────────────────────────────────────
    if not no_review:
        # If reviewing pre-existing artifacts, reconstruct plan_data from
        # the files on disk so the LLM has context when regenerating.
        if plan_data is None:
            plan_data = _load_plan_data_from_workspace(workspace)

        while True:
            approved, feedback = review_references(workspace, schema)
            if approved:
                break
            if feedback == "SKIP":
                return _err("Skipped by reviewer")

            # Regenerate Phase 1 with reviewer feedback
            if not policy_spec:
                print("  Cannot regenerate — no policy_spec.md. Skipping.")
                return _err("Review rejected but no policy_spec for regeneration")

            print("\n  Regenerating with reviewer feedback...")
            t1 = time.monotonic()
            try:
                plan_data = generate_references(
                    client, model, schema, policy_spec,
                    feedback=feedback,
                    previous_plan=plan_data,
                )
                write_phase1_artifacts(workspace, plan_data)
                regen_time = time.monotonic() - t1
                phase1_time += regen_time
                n_checks = len(plan_data["checks"])
                n_refs = len(plan_data.get("references", {}))
                print(f"  Regenerated {n_checks} checks, {n_refs} reference policies ({regen_time:.1f}s)")
            except Exception as e:
                phase1_time += time.monotonic() - t1
                print(f"  Regeneration failed: {e}")
                print("  Retrying review with previous artifacts...")
    else:
        print("\n--- Review: skipped (--no-review) ---")

    # ── Phase 2: CEGIS Synthesis Loop ─────────────────────────────────────
    print("\n--- Phase 2: CEGIS Synthesis Loop ---")
    t2 = time.monotonic()

    try:
        checks = load_checks(workspace)
    except Exception as e:
        return _err(f"Failed to load verification plan: {e}", p1=round(phase1_time, 2))

    checks_total = len(checks)
    print(f"  Checks loaded: {checks_total}")

    # Build initial conversation
    initial_prompt = _format_initial_prompt(schema, policy_spec, checks)
    messages = [{"role": "user", "content": initial_prompt}]

    iteration_log = []
    candidate_text = None

    for iteration in range(1, max_iters + 1):
        print(f"\n  --- Iteration {iteration}/{max_iters} ---")

        # ── LLM synthesis call ──
        try:
            response = client.messages.create(
                model=model,
                max_tokens=4096,
                system=PHASE2_SYSTEM,
                messages=messages,
            )
            candidate_text = _strip_cedar_fencing(response.content[0].text)
        except Exception as e:
            print(f"  LLM error: {e}")
            iteration_log.append(asdict(IterationLog(
                iteration=iteration, loss=-1, checks_passed=0,
                checks_total=checks_total, solver_time_s=0.0,
                counterexample_count=0, syntax_valid=False, status="llm_error",
            )))
            break

        messages.append({"role": "assistant", "content": candidate_text})

        # ── Write candidate + verify ──
        with open(os.path.join(workspace, "candidate.cedar"), "w") as f:
            f.write(candidate_text)

        vr = run_verification(workspace)

        # Classify result
        is_syntax_err = (
            len(vr.results) == 1
            and vr.results[0].check_type == "syntax"
            and not vr.results[0].passed
        )
        cx_count = sum(1 for r in vr.results if not r.passed and r.counterexample)
        passed = sum(1 for r in vr.results if r.passed)

        if vr.loss == 0:
            status = "pass"
        elif is_syntax_err:
            status = "syntax_error"
        else:
            status = "fail"

        log_entry = IterationLog(
            iteration=iteration,
            loss=vr.loss,
            checks_passed=passed,
            checks_total=checks_total,
            solver_time_s=round(vr.solver_time_s, 3),
            counterexample_count=cx_count,
            syntax_valid=not is_syntax_err,
            status=status,
        )
        iteration_log.append(asdict(log_entry))

        # Print status
        if is_syntax_err:
            print(f"  SYNTAX ERROR  solver: {vr.solver_time_s:.2f}s")
        else:
            print(f"  loss: {vr.loss}/{checks_total}  solver: {vr.solver_time_s:.2f}s")
        for r in vr.results:
            mark = "PASS" if r.passed else "FAIL"
            print(f"    {r.check_name}: {mark}")

        if vr.loss == 0:
            print(f"\n  CONVERGED in {iteration} iteration(s)")
            # Append to policy store
            store_path = os.path.join(workspace, "policy_store.cedar")
            with open(store_path, "a") as f:
                f.write(f"\n// --- Verified (eval iteration {iteration}) ---\n")
                f.write(candidate_text + "\n")
            break

        # ── Feedback for next iteration ──
        feedback = _format_feedback(vr)
        messages.append({"role": "user", "content": feedback})

        # Trim conversation to avoid context limits: keep first message + last 8
        if len(messages) > 12:
            messages = messages[:1] + messages[-8:]

    phase2_time = time.monotonic() - t2
    total_time = time.monotonic() - t_start
    final_loss = iteration_log[-1]["loss"] if iteration_log else -1

    result = ScenarioResult(
        scenario=scenario_name,
        model=model,
        converged=(final_loss == 0),
        iterations=len(iteration_log),
        max_iterations=max_iters,
        total_time_s=round(total_time, 2),
        phase1_time_s=round(phase1_time, 2),
        phase2_time_s=round(phase2_time, 2),
        final_loss=final_loss,
        checks_total=checks_total,
        iteration_log=iteration_log,
    )

    # Persist per-scenario log
    with open(os.path.join(workspace, "eval_log.json"), "w") as f:
        json.dump(asdict(result), f, indent=2)

    return result


# ---------------------------------------------------------------------------
# Scenario discovery
# ---------------------------------------------------------------------------

def discover_scenarios() -> list[str]:
    """Find all runnable scenarios under experiments/, workspace/, and dataset/."""
    scenarios = []

    # Experiments (fully configured)
    exp_dir = os.path.join(ROOT_DIR, "experiments")
    if os.path.isdir(exp_dir):
        for name in sorted(os.listdir(exp_dir)):
            path = os.path.join(exp_dir, name)
            if os.path.isdir(path) and _has_schema(path):
                scenarios.append(path)

    # Workspace (active scenario)
    ws = os.path.join(ROOT_DIR, "workspace")
    if os.path.isdir(ws) and _has_schema(ws):
        scenarios.append(ws)

    # Dataset scenarios
    ds_dir = os.path.join(ROOT_DIR, "dataset")
    if os.path.isdir(ds_dir):
        for name in sorted(os.listdir(ds_dir)):
            path = os.path.join(ds_dir, name)
            if os.path.isdir(path) and _has_schema(path):
                scenarios.append(path)

    return scenarios


def _has_schema(path: str) -> bool:
    return (
        os.path.exists(os.path.join(path, "schema.cedarschema"))
        or os.path.exists(os.path.join(path, "policies.cedarschema"))
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Cedar Synthesis Engine — Evaluation Harness",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  python eval_harness.py --scenario experiments/github
  python eval_harness.py --scenario experiments/github --no-review
  python eval_harness.py --scenario experiments/github --model claude-sonnet-4-20250514 claude-haiku-4-5-20251001 --no-review
  python eval_harness.py --all --gen-references --no-review --max-iters 20
  python eval_harness.py --scenario workspace --run-id my_test_run""",
    )
    parser.add_argument(
        "--scenario", nargs="+", metavar="PATH",
        help="Scenario directory path(s) to evaluate",
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Discover and run all available scenarios",
    )
    parser.add_argument(
        "--model", nargs="+", default=[DEFAULT_MODEL],
        help=f"LLM model(s) for synthesis (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--max-iters", type=int, default=MAX_ITERATIONS,
        help=f"Max CEGIS iterations per scenario (default: {MAX_ITERATIONS})",
    )
    parser.add_argument(
        "--gen-references", action="store_true",
        help="(Re)generate Phase 1 artifacts even if they already exist",
    )
    parser.add_argument(
        "--no-review", action="store_true",
        help="Skip human review of reference policies (for automated benchmarks)",
    )
    parser.add_argument(
        "--run-id", type=str, default=None,
        help="Custom run ID (default: timestamp)",
    )
    args = parser.parse_args()

    # Resolve scenarios
    if args.all:
        scenarios = discover_scenarios()
    elif args.scenario:
        scenarios = [os.path.abspath(p) for p in args.scenario]
    else:
        parser.error("Specify --scenario PATH(s) or --all")

    if not scenarios:
        print("No scenarios found.")
        sys.exit(1)

    models = args.model

    # Create run directory
    run_id = args.run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = os.path.join(EVAL_RUNS_DIR, run_id)
    os.makedirs(run_dir, exist_ok=True)

    print("=" * 60)
    print("CEDAR SYNTHESIS ENGINE — EVALUATION HARNESS")
    print("=" * 60)
    print(f"Run ID:     {run_id}")
    print(f"Model(s):   {', '.join(models)}")
    print(f"Max iters:  {args.max_iters}")
    print(f"Review:     {'disabled' if args.no_review else 'enabled (human-in-the-loop)'}")
    print(f"Scenarios:  {len(scenarios)}")
    for s in scenarios:
        print(f"  - {os.path.relpath(s, ROOT_DIR)}")
    print(f"Output:     {os.path.relpath(run_dir, ROOT_DIR)}")

    # Run each (scenario, model) combination
    all_results = []
    for model in models:
        # When comparing models, namespace run dirs by model
        if len(models) > 1:
            model_run_dir = os.path.join(run_dir, model.replace("/", "_"))
            os.makedirs(model_run_dir, exist_ok=True)
        else:
            model_run_dir = run_dir

        for scenario_path in scenarios:
            result = run_scenario(
                scenario_path=scenario_path,
                run_dir=model_run_dir,
                model=model,
                max_iters=args.max_iters,
                gen_references=args.gen_references,
                no_review=args.no_review,
            )
            all_results.append(asdict(result))

    # Save summary
    summary = {
        "run_id": run_id,
        "models": models,
        "max_iterations": args.max_iters,
        "gen_references": args.gen_references,
        "human_review": not args.no_review,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "results": all_results,
    }
    summary_path = os.path.join(run_dir, "summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    # Print summary table
    print(f"\n\n{'=' * 70}")
    print("SUMMARY")
    print(f"{'=' * 70}")

    header = f"{'Scenario':<22} {'Model':<28} {'Result':<8} {'Iters':<7} {'Loss':<5} {'Time':<7}"
    print(header)
    print("-" * 70)

    for r in all_results:
        if r.get("error"):
            status = "ERROR"
        elif r["converged"]:
            status = "PASS"
        else:
            status = "FAIL"

        model_short = r["model"].split("/")[-1]
        if len(model_short) > 26:
            model_short = model_short[:24] + ".."

        iters = f"{r['iterations']}/{r['max_iterations']}"
        t = f"{r['total_time_s']:.1f}s"
        print(f"{r['scenario']:<22} {model_short:<28} {status:<8} {iters:<7} {r['final_loss']:<5} {t:<7}")

    converged = sum(1 for r in all_results if r["converged"])
    total = len(all_results)
    print("-" * 70)
    print(f"Converged: {converged}/{total}")
    print(f"Results:   {os.path.relpath(summary_path, ROOT_DIR)}")

    if any(r.get("error") for r in all_results):
        print("\nErrors:")
        for r in all_results:
            if r.get("error"):
                print(f"  {r['scenario']} ({r['model']}): {r['error']}")

    return 0 if converged == total else 1


if __name__ == "__main__":
    sys.exit(main())
