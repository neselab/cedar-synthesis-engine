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
import hashlib
import json
import os
import re
import shutil
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from anthropic import Anthropic

from orchestrator import load_checks, run_verification
from solver_wrapper import CheckResult, VerificationResult, run_syntax_check

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
EVAL_RUNS_DIR = os.path.join(ROOT_DIR, "eval_runs")

DEFAULT_MODEL = "claude-sonnet-4-20250514"
DEFAULT_PHASE1_MODEL = "claude-opus-4-6"  # Phase 1 is a heavy one-shot reasoning task
MAX_ITERATIONS = 20

# Pricing per million tokens (USD)
MODEL_PRICING = {
    "claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.00},
    "claude-sonnet-4-20250514": {"input": 3.00, "output": 15.00},
    "claude-opus-4-20250514": {"input": 15.00, "output": 75.00},
    "claude-opus-4-6": {"input": 15.00, "output": 75.00},
}


def _estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate cost in USD for given token counts."""
    pricing = MODEL_PRICING.get(model, {"input": 3.00, "output": 15.00})
    return (input_tokens * pricing["input"] + output_tokens * pricing["output"]) / 1_000_000


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
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass
class ScenarioResult:
    scenario: str
    model: str              # phase2 model (primary — used for comparison runs)
    phase1_model: str
    phase2_model: str
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
    phase1_input_tokens: int = 0
    phase1_output_tokens: int = 0
    phase2_input_tokens: int = 0
    phase2_output_tokens: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0


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
- Reference policies must be valid Cedar syntax AND must pass Cedar's
  type-checker (`cedar validate`). Both gates run on every reference file
  before Phase 2 starts.
- Use exact entity types, actions, and attribute names from the schema.
- For "always-denies-liveness" checks, omit the "reference_file" field.
- Each reference file should contain exactly one permit or forbid statement.

Cedar gotchas you MUST avoid:
- **Optional attributes**: any attribute declared with `?` in the schema
  (e.g. `context: { targetUser?: User }`) MAY be absent. Cedar's type-checker
  REQUIRES every read of such an attribute to be guarded with the POSITIVE
  `has` form. The negated form is NOT recognized:

      // CORRECT — type-checker accepts this
      context has targetUser && context.targetUser.job == Job::"customer"

      // WRONG — type-checker REJECTS this even though it's logically equivalent
      !(context has targetUser) || context.targetUser.job != Job::"customer"

  When you need "if the attribute is present, it must satisfy P", write it as
  `(!(context has X)) || (context has X && P)` so the type-checker sees a
  positive `has` guard adjacent to every read. Do NOT rely on negation
  short-circuit propagation — Cedar's type-checker does not propagate it.
- **Type constraints use `is`, not `:`**: write `principal is User`, never
  `principal: User`."""


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
    usage = (response.usage.input_tokens, response.usage.output_tokens)
    return _extract_json(response.content[0].text), usage


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
# Phase 1.25: Reference self-validation (catches broken references before
# they poison Phase 2)
# ---------------------------------------------------------------------------

def _validate_references(workspace: str) -> list[tuple[str, str]]:
    """Run `cedar validate` on every reference in workspace/references/.

    Returns a list of (filename, error_text) for references that fail.
    Empty list means all references are clean.
    """
    refs_dir = os.path.join(workspace, "references")
    schema_path = os.path.join(workspace, "schema.cedarschema")
    if not os.path.isdir(refs_dir):
        return []

    broken: list[tuple[str, str]] = []
    for fname in sorted(os.listdir(refs_dir)):
        if not fname.endswith(".cedar"):
            continue
        fpath = os.path.join(refs_dir, fname)
        ok, err, kind = run_syntax_check(schema_path, fpath)
        if not ok:
            broken.append((fname, err))
    return broken


def _format_phase1_validation_feedback(
    broken: list[tuple[str, str]],
    plan_data: dict,
) -> str:
    """Build a self-correction prompt listing every broken reference.

    Includes the file content, the cedar error output, and explicit guidance
    on the most common pitfall (negated `has` guards on optional attrs).
    """
    parts = [
        f"## Phase 1 Reference Validation FAILED — {len(broken)} reference(s) broken\n",
        "Cedar's type-checker rejected the following reference policies you "
        "generated. Fix them and re-emit the COMPLETE plan_data JSON.\n",
    ]

    references = plan_data.get("references", {})
    for fname, err in broken:
        content = references.get(fname, "<missing>")
        parts.append(f"### `{fname}`")
        parts.append("Current content:")
        parts.append("```cedar")
        parts.append(content.strip())
        parts.append("```")
        parts.append("Cedar validator output:")
        parts.append("```")
        parts.append(err[:1500])
        parts.append("```")

        # Detect optional-attribute pattern and add tailored advice
        if "optional" in err and "attribute" in err:
            optional_attrs = []
            for m in re.finditer(r"optional\s+attribute\s+`([^`]+)`", err):
                if m.group(1) not in optional_attrs:
                    optional_attrs.append(m.group(1))
            attrs_str = ", ".join(f"`{a}`" for a in optional_attrs) or "(unknown)"
            parts.append(
                f"**ROOT CAUSE: unguarded optional attribute(s) {attrs_str}**\n"
                "Cedar's type-checker does NOT recognize the negated form:\n"
                "  WRONG: `!(context has X) || context.X.field == ...`\n"
                "  RIGHT: `!(context has X) || (context has X && context.X.field == ...)`\n"
                "Or equivalently in pure positive form:\n"
                "  RIGHT: `(context has X => context.X.field == ...)` "
                "(rewritten as `(!(context has X) || (context has X && ...))`)\n"
                "Every single read of an optional attribute MUST sit inside a "
                "branch where `context has X` is positively asserted.\n"
            )
        parts.append("")

    parts.append(
        "Re-emit the COMPLETE JSON (all checks + all references), with the "
        "broken reference files corrected. Keep all other references and "
        "checks unchanged."
    )
    return "\n".join(parts)


def self_validate_references(
    client,
    model: str,
    workspace: str,
    schema: str,
    policy_spec: str,
    plan_data: dict,
    max_rounds: int = 3,
) -> tuple[dict, int, int, int]:
    """Validate every generated reference; iteratively ask the LLM to fix
    broken ones.

    Returns (final_plan_data, extra_in_tokens, extra_out_tokens, n_rounds).
    """
    extra_in = 0
    extra_out = 0
    rounds = 0
    for r in range(1, max_rounds + 1):
        broken = _validate_references(workspace)
        if not broken:
            return plan_data, extra_in, extra_out, rounds
        rounds = r
        print(
            f"  Phase 1.25: {len(broken)} broken reference(s) — "
            f"requesting fix (round {r}/{max_rounds})"
        )
        for fname, err in broken:
            first_line = err.strip().split("\n", 1)[0]
            print(f"    - {fname}: {first_line[:80]}")

        feedback = _format_phase1_validation_feedback(broken, plan_data)
        try:
            new_plan, usage = generate_references(
                client, model, schema, policy_spec,
                feedback=feedback,
                previous_plan=plan_data,
            )
            extra_in += usage[0]
            extra_out += usage[1]
            plan_data = new_plan
            write_phase1_artifacts(workspace, plan_data)
        except Exception as e:
            print(f"    Phase 1.25 LLM call failed: {e}")
            break

    # Final check
    final_broken = _validate_references(workspace)
    if final_broken:
        print(
            f"  Phase 1.25: WARNING — {len(final_broken)} reference(s) still "
            f"broken after {rounds} fix round(s); Phase 2 will likely fail "
            f"these checks"
        )
    else:
        print(f"  Phase 1.25: all references type-check ✓")

    return plan_data, extra_in, extra_out, rounds


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
  context.field                 // request context

Floor checks (your policy must PERMIT at least what a reference policy permits):
- A floor failure means a specific (principal, action, resource) is permitted by
  the floor but denied by your policy. Your policy is OVER-RESTRICTIVE.
- The most common cause is an EXTRA condition in your permit rule that is not in
  the floor, OR a forbid rule that fires for the floor's tuple.

ROLE INTERSECTION TRAP — read this carefully, it is the most common floor failure:
- Cedar entities can be in MULTIPLE roles simultaneously. A user can be both a
  ClinicalResearcher and a PrincipalInvestigator, both an Auditor and a Manager.
  Floor references generally constrain only ONE role and do not exclude others.
- A SPEC LINE like "Role Y is blocked from action A on resource type R" is most
  cleanly encoded by EXCLUDING R from Y's permit rule (e.g., adding
  `resource.attr != "R"` to the Y permit rule). It is NOT cleanly encoded as
  `forbid action A when principal in Role::"Y" && resource.attr == "R"`,
  because that forbid will ALSO fire for any user who is in Y AND in some other
  role X that the floor for X says must be allowed to perform A on R. The
  forbid form will fail floor_x checks every time, and there is no way to
  rewrite the X permit to satisfy the floor while the Y-keyed forbid exists.
- Equivalent trap on the permit side: a permit `when principal in Role::"X" &&
  !(principal in Role::"Y")` denies any user in BOTH X and Y. If the X-role
  floor reference does not include `!(principal in Role::"Y")`, your permit is
  over-restrictive. REMOVE the negation.
- Rule of thumb: if a spec line says "role Y is blocked from R", do NOT write a
  forbid keyed on `principal in Role::"Y"`. Instead, ensure the Y permit rule
  itself excludes R. Then leave the X, Z, etc. permit rules alone — they will
  correctly grant access to multi-role users.
- This is the SINGLE most common cause of floor failures that oscillate with
  ceiling failures. If you see floor_pi or floor_cr or floor_dm failing while
  some `xxx_blocks_yyy_role` ceiling also fails, you are in this trap. Fix it
  by moving the role restriction OUT of the forbid and INTO the role's permit."""


def _strip_cedar_fencing(text: str) -> str:
    """Extract Cedar policy code from LLM output.

    Handles multiple output formats:
    1. Raw Cedar code (no fencing)
    2. Code wrapped in ```cedar ... ``` or ``` ... ```
    3. Code wrapped with explanatory text before/after the fence
    4. Multiple code blocks (extracts and joins all of them)
    """
    text = text.strip()

    # Try to extract fenced code blocks (```cedar ... ``` or ``` ... ```)
    blocks = re.findall(r"```(?:cedar)?\s*\n(.*?)```", text, re.DOTALL)
    if blocks:
        # Join all code blocks (model might split across multiple fences)
        return "\n\n".join(b.strip() for b in blocks if b.strip())

    # No fenced blocks found — check if the whole output looks like Cedar
    # (starts with permit/forbid or a comment)
    lines = text.split("\n")
    cedar_lines = []
    in_cedar = False
    for line in lines:
        stripped = line.strip()
        # Cedar policy lines start with these keywords or are continuations
        if stripped.startswith(("permit", "forbid", "//", "when", "unless",
                               "}", "{", "&&", "||", "principal", "action",
                               "resource", "context")):
            in_cedar = True
        elif stripped == "" and in_cedar:
            pass  # blank lines between rules are fine
        elif stripped.startswith((")", ");")) and in_cedar:
            pass  # closing parens
        elif in_cedar and not stripped[0:1].isalpha():
            pass  # continuation lines (indented conditions etc.)
        elif in_cedar and stripped:
            # Non-Cedar text after Cedar started — might be explanation
            # Only break if it looks like natural language (no Cedar operators)
            if not any(kw in stripped for kw in ["==", "in ", "::", ".", "{"]):
                in_cedar = False
                continue

        if in_cedar:
            cedar_lines.append(line)

    if cedar_lines:
        return "\n".join(cedar_lines).strip()

    # Fallback: return as-is with simple fence removal
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


def _format_syntax_feedback(error_text: str) -> str:
    """
    Parse and deduplicate cedar validate error output.

    Cedar validate repeats the same error for every occurrence (e.g., 32 times
    for 16 rules each with 2 type constraints). This compresses 18K+ chars of
    repetitive output into ~500 chars of structured, actionable feedback.
    """
    if not error_text:
        return "Unknown syntax error."

    # Split into individual error blocks (cedar uses × or "error" markers)
    # Each error block starts with × or "  ×"
    lines = error_text.split("\n")

    # Extract unique error messages and help texts
    error_counts: dict[str, int] = {}
    help_texts: dict[str, str] = {}
    first_snippets: dict[str, str] = {}

    current_error = ""
    current_snippet_lines: list[str] = []
    in_snippet = False

    for line in lines:
        stripped = line.strip()

        # Detect error message lines (cedar format: "× message" or "╰─▶ message")
        if stripped.startswith("×") or stripped.startswith("╰─▶"):
            # Extract the core error message
            msg = stripped.lstrip("× ").lstrip("╰─▶ ").strip()
            if msg and msg != "policy set validation failed" and msg != "failed to parse policy set":
                current_error = msg
                error_counts[msg] = error_counts.get(msg, 0) + 1
                current_snippet_lines = []
                in_snippet = True

        # Detect help lines
        elif stripped.startswith("help:"):
            help_msg = stripped[5:].strip()
            if current_error and current_error not in help_texts:
                help_texts[current_error] = help_msg

        # Capture code snippet (cedar uses ╭ │ · ╰ and line numbers)
        elif in_snippet and (stripped.startswith("╭") or stripped.startswith("│")
                            or stripped.startswith("·") or stripped.startswith("╰")
                            or (len(stripped) > 0 and stripped[0].isdigit())):
            current_snippet_lines.append(line)
            if stripped.startswith("╰"):
                in_snippet = False
                if current_error and current_error not in first_snippets:
                    first_snippets[current_error] = "\n".join(current_snippet_lines)

    if not error_counts:
        # Fallback: couldn't parse, return truncated raw output
        truncated = error_text[:800]
        if len(error_text) > 800:
            truncated += f"\n... ({len(error_text) - 800} more characters truncated)"
        return truncated

    # Build compact structured feedback
    parts = []
    for msg, count in error_counts.items():
        if count > 1:
            parts.append(f"**{count} occurrences of:** {msg}")
        else:
            parts.append(f"**Error:** {msg}")

        if msg in help_texts:
            parts.append(f"  Fix: {help_texts[msg]}")

        if msg in first_snippets:
            parts.append(f"  Example (first occurrence):")
            parts.append(f"  ```")
            parts.append(f"  {first_snippets[msg].strip()}")
            parts.append(f"  ```")

        parts.append(f"  Fix ALL occurrences of this pattern throughout your policy.\n")

    return "\n".join(parts)


def _format_validation_feedback(error_text: str) -> str:
    """
    Format Cedar's *type-checker / validator* errors (returncode 3).

    These look syntactically OK to the parser but the type-checker rejected
    them. Most common cause: accessing an *optional* attribute on `context`
    or an entity without first guarding it with `has`.

    Example error from `cedar validate`:

        × policy set validation failed
        ╰─▶ for policy `policy8`, unable to guarantee safety of access to
            optional attribute `targetUser` in context for
            Action::"grantViewAccessToTemplate"
    """
    if not error_text:
        return "Unknown validation error."

    # Detect the optional-attribute case so we can produce a hyper-targeted
    # fix; this is by far the most common Cedar type-check failure.
    # Cedar wraps long error messages, so allow whitespace (including
    # newlines) between "optional" and "attribute".
    optional_attrs: list[str] = []
    for match in re.finditer(
        r"optional\s+attribute\s+`([^`]+)`", error_text
    ):
        attr = match.group(1)
        if attr not in optional_attrs:
            optional_attrs.append(attr)

    parts = []
    parts.append("**TYPE-CHECK / VALIDATION ERROR — your policy parses, but Cedar's validator rejected it.**")
    parts.append("This is NOT a parse error. Do NOT change `principal is User` or rule structure.")
    parts.append("Cedar's type-checker found that your policy could fail at runtime.\n")

    if optional_attrs:
        parts.append(
            "**Root cause: unguarded access to OPTIONAL attribute(s): "
            + ", ".join(f"`{a}`" for a in optional_attrs)
            + "**"
        )
        parts.append("")
        parts.append("In Cedar, optional attributes (declared with `?` in the schema, e.g.")
        parts.append("`context: { targetUser?: User }`) MAY be absent from a request. You")
        parts.append("MUST guard every access with `has` BEFORE you read the attribute.")
        parts.append("")
        parts.append("CORRECT pattern:")
        parts.append("```cedar")
        for a in optional_attrs:
            # Strip "context." or entity prefix if present, just for example shape
            base = a.split(".")[-1]
            parts.append(
                f"  // before reading `{a}`, guard it:"
            )
            parts.append(
                f"  context has {base} && context.{base}.someField == \"X\""
            )
        parts.append("```")
        parts.append("")
        parts.append("WRONG pattern (what your policy currently does):")
        parts.append("```cedar")
        parts.append(f"  context.{optional_attrs[0].split('.')[-1]}.someField == \"X\"   // unsafe — attribute may be absent")
        parts.append("```")
        parts.append("")
        parts.append(
            "Wrap EVERY read of these attributes in `(context has X && ...)` or use a `when` "
            "clause guard. Adding the guard back is REQUIRED — removing it to satisfy a "
            "different check will just bring this error back."
        )
        parts.append("")

    # Always include the truncated raw cedar output so the model can see line numbers.
    snippet = error_text[:1200]
    if len(error_text) > 1200:
        snippet += f"\n... ({len(error_text) - 1200} more characters truncated)"
    parts.append("Raw validator output:")
    parts.append("```")
    parts.append(snippet)
    parts.append("```")

    return "\n".join(parts)


def _format_feedback(
    vr: VerificationResult,
    checks: list[dict],
    prev_failed: set[str] | None = None,
    repeat_info: dict | None = None,
    candidate_text: str | None = None,
) -> str:
    """
    Build a rich feedback message from verification results.

    Includes:
    - The reference policy for each failed check (so the model can see the bound)
    - Directional explanation (too permissive vs too restrictive)
    - Oscillation warnings when a fix regresses previously-passing checks
    - Hash-based oscillation warnings when the same policy is resubmitted
      (often happens when the model cycles between gate categories)
    - Structured, deduplicated syntax error feedback
    - Role-intersection diagnosis when candidate has forbid rules keyed on role
      membership and a floor check fails (the most common floor-failure cause)
    - Type-check / validation feedback (distinct from parse errors) with
      targeted help for unguarded optional attributes
    """
    # Map check names to their definitions
    check_map = {c["name"]: c for c in checks}

    failed_now = {r.check_name for r in vr.results if not r.passed}
    parts = [f"## Verification Results — {vr.loss} check(s) FAILED\n"]

    # Hash-based repeat / cross-gate oscillation detection (strongest signal)
    if repeat_info is not None:
        parts.append("**🛑 STOP — REPEATED POLICY DETECTED 🛑**")
        parts.append(
            f"You just submitted a byte-identical policy to the one you "
            f"submitted at iteration {repeat_info['first_iter']}. You are "
            f"in a loop."
        )
        union = repeat_info.get("window_union", [])
        if union:
            parts.append("")
            parts.append(
                "Across all your recent attempts, the following failure modes "
                "have appeared (sometimes alternating between iterations):"
            )
            for name in union:
                parts.append(f"  - {name}")
            parts.append("")
            parts.append(
                "**Every single one of these must be fixed AT THE SAME TIME, "
                "in ONE policy.** You cannot fix one by trading off another. "
                "Do not remove a guard (`has`, `==`, role check) to satisfy a "
                "different check — that just sends the previous failure back. "
                "Reason about the conjunction of constraints, not one at a time."
            )
            parts.append("")

    # Set-based oscillation detection (existing — kept as a softer signal)
    if prev_failed is not None and repeat_info is None:
        fixed = prev_failed - failed_now
        regressed = failed_now - prev_failed
        if fixed and regressed:
            parts.append(f"**WARNING — OSCILLATION DETECTED**")
            parts.append(f"You fixed: {', '.join(sorted(fixed))}")
            parts.append(f"But broke: {', '.join(sorted(regressed))}")
            parts.append(f"ALL checks must pass simultaneously. "
                         f"Do not sacrifice one bound to satisfy another.\n")

    for r in vr.results:
        mark = "PASS" if r.passed else "FAIL"
        parts.append(f"- {r.check_name} ({r.check_type}): **{mark}**")

        if r.passed:
            continue

        check_def = check_map.get(r.check_name, {})
        ctype = check_def.get("type", r.check_type)

        # Directional explanation + reference policy
        if ctype == "syntax":
            parts.append(f"  **SYNTAX / PARSE ERROR — your policy failed to parse.**")
            parts.append(f"  No semantic checks can run until syntax is valid.")
            parts.append(f"  Fix the parse errors below, then resubmit.\n")
            if r.counterexample:
                parts.append(_format_syntax_feedback(r.counterexample))
        elif ctype == "validation":
            # Distinct from "syntax" — the policy parses, but Cedar's validator
            # rejected it (e.g. unguarded optional attribute access).
            if r.counterexample:
                parts.append(_format_validation_feedback(r.counterexample))
            else:
                parts.append("  **VALIDATION ERROR — Cedar's type-checker rejected the policy.**")
        elif ctype == "implies":
            ref_path = check_def.get("reference_path", "")
            parts.append(f"  **Your policy is MORE permissive than the ceiling.**")
            parts.append(f"  It allows something the ceiling forbids. Tighten conditions.")
            if ref_path and os.path.exists(ref_path):
                with open(ref_path) as f:
                    parts.append(f"  Ceiling policy (your policy must not exceed this):")
                    parts.append(f"  ```cedar\n  {f.read().strip()}\n  ```")
            if r.counterexample:
                parts.append(f"  Counterexample from solver:\n  ```\n  {r.counterexample}\n  ```")
        elif ctype == "floor":
            floor_path = check_def.get("floor_path", "")
            parts.append(f"  **Your policy is MORE restrictive than the floor.**")
            parts.append(f"  It denies something that MUST be allowed. Loosen conditions.")
            floor_text = ""
            if floor_path and os.path.exists(floor_path):
                with open(floor_path) as f:
                    floor_text = f.read().strip()
                parts.append(f"  Floor policy (your policy must allow at least this):")
                parts.append(f"  ```cedar\n  {floor_text}\n  ```")
            # Structural hint: detect the role-intersection trap. The floor's
            # permitted set may include users who are in multiple roles, but
            # the candidate may have a forbid rule (or a permit-rule negation)
            # keyed on role membership that fires for those multi-role users.
            # Scan the candidate text for the smoking gun and call it out.
            if candidate_text:
                import re as _re
                # Forbid rules that mention `principal in Role::"..."` (or Group)
                forbid_role_hits: list[str] = []
                for m in _re.finditer(
                    r"forbid\s*\([^)]*\)\s*when\s*\{[^}]*?principal\s+in\s+(?:Role|Group)::\"([^\"]+)\"",
                    candidate_text,
                    _re.DOTALL,
                ):
                    forbid_role_hits.append(m.group(1))
                # Permit rules with `!(principal in Role::"...")`
                permit_neg_hits: list[str] = []
                for m in _re.finditer(
                    r"!\s*\(\s*principal\s+in\s+(?:Role|Group)::\"([^\"]+)\"",
                    candidate_text,
                ):
                    permit_neg_hits.append(m.group(1))
                if forbid_role_hits or permit_neg_hits:
                    parts.append(
                        "  ROLE-INTERSECTION DIAGNOSIS: your current candidate "
                        "contains role-keyed restrictions that are the most "
                        "common cause of floor failures."
                    )
                    if forbid_role_hits:
                        uniq = sorted(set(forbid_role_hits))
                        parts.append(
                            f"    - You have `forbid` rule(s) keyed on "
                            f"`principal in Role::\"{', '.join(uniq)}\"`. These "
                            f"forbids fire for ANY user in that role, including "
                            f"users who are ALSO in other roles that the floor "
                            f"says must be permitted. If a spec line says "
                            f"\"role X is blocked from R\", encode it by "
                            f"excluding R from X's PERMIT rule, NOT with a "
                            f"forbid keyed on `in Role::\"X\"`. Move the "
                            f"restriction OUT of the forbid and INTO the X "
                            f"permit rule's conditions."
                        )
                    if permit_neg_hits:
                        uniq = sorted(set(permit_neg_hits))
                        parts.append(
                            f"    - You have permit rule(s) with "
                            f"`!(principal in Role::\"{', '.join(uniq)}\")`. "
                            f"REMOVE these negations — Cedar entities can be in "
                            f"multiple roles, and the floor reference does not "
                            f"contain this exclusion. The negation denies "
                            f"floor-permitted users who happen to also be in "
                            f"the excluded role."
                        )
            if r.counterexample:
                parts.append(f"  Counterexample from solver:\n  ```\n  {r.counterexample}\n  ```")
        elif "liveness" in ctype:
            parts.append(f"  **Your policy denies ALL requests for this action.**")
            parts.append(f"  At least one scenario must be permitted.")
            if r.counterexample:
                parts.append(f"  Counterexample from solver:\n  ```\n  {r.counterexample}\n  ```")
        else:
            if r.counterexample:
                parts.append(f"  Counterexample from solver:\n  ```\n  {r.counterexample}\n  ```")

    parts.append(
        "\nFix the policy to address EVERY failure without breaking passing checks. "
        "Output the COMPLETE updated policy."
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
    phase1_model: str,
    phase2_model: str,
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
    print(f"Phase 1:  {phase1_model}")
    print(f"Phase 2:  {phase2_model}")
    print(f"{'=' * 60}")

    def _err(msg: str, **kw) -> ScenarioResult:
        return ScenarioResult(
            scenario=scenario_name, model=phase2_model,
            phase1_model=phase1_model, phase2_model=phase2_model,
            converged=False,
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

    # ── Phase 0.5: Schema sanity check ────────────────────────────────────
    # Validate the schema against an empty policy file. If the schema itself
    # doesn't parse, every downstream reference / candidate will "fail" with
    # the same schema error, Phase 1.25 will burn its self-correction rounds
    # blaming the LLM, and Phase 2 will hit a syntax-error loop. None of that
    # is the model's fault — the scenario is malformed. Detect it here and
    # abort with a clear error so the run summary shows the real cause.
    _empty_policy = os.path.join(workspace, "_empty_policy_for_schema_check.cedar")
    with open(_empty_policy, "w") as _f:
        _f.write("// schema sanity check\n")
    _ok, _err_msg, _err_kind = run_syntax_check(schema_path, _empty_policy)
    try:
        os.remove(_empty_policy)
    except OSError:
        pass
    if not _ok and _err_kind == "parse" and "schema" in _err_msg.lower():
        # cedar validate's parse error against an empty policy is *always*
        # a schema-level problem (the policy file has nothing to misparse).
        first_line = _err_msg.strip().split("\n", 1)[0][:200]
        return _err(
            f"Scenario schema is malformed (Cedar parse error): {first_line}"
        )

    spec_path = os.path.join(workspace, "policy_spec.md")
    policy_spec = ""
    if os.path.exists(spec_path):
        with open(spec_path) as f:
            policy_spec = f.read()

    # ── Phase 0.55: Spec sanity check ─────────────────────────────────────
    # Some scenario directories were generated with a placeholder spec that
    # just points at a separate ground-truth Cedar file ("See the ground-
    # truth policy in dataset/.../policies.cedar for reference"). The
    # synthesizer cannot read that file — it only sees policy_spec.md — so
    # the scenario silently runs with no requirements at all and Haiku has
    # to invent semantics from the schema. Detect this and abort cleanly.
    #
    # Heuristic: a real spec is at least ~10 substantive lines and does not
    # contain the placeholder template phrase. Both checks are needed: the
    # phrase alone could appear in a long real spec as a citation, and the
    # length alone could be defeated by a short-but-real spec.
    if policy_spec:
        _spec_substantive_lines = sum(
            1 for ln in policy_spec.splitlines() if ln.strip()
        )
        _placeholder_phrase = "see the ground-truth policy in"
        if (
            _placeholder_phrase in policy_spec.lower()
            and _spec_substantive_lines < 10
        ):
            first_real = next(
                (ln.strip() for ln in policy_spec.splitlines() if ln.strip()),
                "",
            )
            return _err(
                "Scenario spec is a placeholder, not a real requirements "
                "document. The synthesizer would have to invent semantics "
                "from the schema alone. First line: " + first_real[:120]
            )

    client = Anthropic()

    # ── Phase 1: Reference Generation ─────────────────────────────────────
    phase1_time = 0.0
    phase1_in_tok = 0
    phase1_out_tok = 0
    vp_exists = os.path.exists(os.path.join(workspace, "verification_plan.py"))
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
            plan_data, usage = generate_references(client, phase1_model, schema, policy_spec, example_plan)
            phase1_in_tok += usage[0]
            phase1_out_tok += usage[1]
            write_phase1_artifacts(workspace, plan_data)
            phase1_time = time.monotonic() - t1
            n_checks = len(plan_data["checks"])
            n_refs = len(plan_data.get("references", {}))
            print(f"  Generated {n_checks} checks, {n_refs} reference policies ({phase1_time:.1f}s)")

            # Phase 1.25: validate every reference and self-correct broken ones
            plan_data, sv_in, sv_out, sv_rounds = self_validate_references(
                client, phase1_model, workspace, schema, policy_spec, plan_data,
            )
            phase1_in_tok += sv_in
            phase1_out_tok += sv_out
            phase1_time = time.monotonic() - t1
        except Exception as e:
            phase1_time = time.monotonic() - t1
            return _err(f"Phase 1 failed: {e}", p1=round(phase1_time, 2))
    else:
        print("\n--- Phase 1: Using existing verification plan ---")
        # Even when reusing an existing plan, ensure references type-check.
        # If they don't, run the self-correction loop (cheap when refs are
        # already clean — only one validate pass).
        if not gen_references:
            t1 = time.monotonic()
            _existing_broken = _validate_references(workspace)
            if _existing_broken:
                print(
                    f"  Phase 1.25: existing plan has {len(_existing_broken)} "
                    f"broken reference(s) — running self-correction"
                )
                if plan_data is None:
                    plan_data = _load_plan_data_from_workspace(workspace)
                plan_data, sv_in, sv_out, _ = self_validate_references(
                    client, phase1_model, workspace, schema, policy_spec, plan_data,
                )
                phase1_in_tok += sv_in
                phase1_out_tok += sv_out
            phase1_time += time.monotonic() - t1

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
                plan_data, usage = generate_references(
                    client, phase1_model, schema, policy_spec,
                    feedback=feedback,
                    previous_plan=plan_data,
                )
                phase1_in_tok += usage[0]
                phase1_out_tok += usage[1]
                write_phase1_artifacts(workspace, plan_data)
                regen_time = time.monotonic() - t1
                phase1_time += regen_time
                n_checks = len(plan_data["checks"])
                n_refs = len(plan_data.get("references", {}))
                print(f"  Regenerated {n_checks} checks, {n_refs} reference policies ({regen_time:.1f}s)")

                # Phase 1.25 also runs after reviewer-driven regeneration
                plan_data, sv_in, sv_out, _ = self_validate_references(
                    client, phase1_model, workspace, schema, policy_spec, plan_data,
                )
                phase1_in_tok += sv_in
                phase1_out_tok += sv_out
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
    prev_failed: set[str] | None = None     # for oscillation detection
    # Hash-based oscillation detection across gate categories.
    # Maps sha256(candidate_text) → (first_iter_seen, failed_check_names_at_that_iter).
    # When the same hash recurs we know the model is cycling, even if the
    # failure mode flips between syntax/validation/semantic gates.
    seen_hashes: dict[str, tuple[int, list[str]]] = {}
    failure_history: list[set[str]] = []     # union-of-failures across all iters
    phase2_in_tok = 0
    phase2_out_tok = 0

    for iteration in range(1, max_iters + 1):
        print(f"\n  --- Iteration {iteration}/{max_iters} ---")

        # ── LLM synthesis call ──
        iter_in_tok = 0
        iter_out_tok = 0
        try:
            response = client.messages.create(
                model=phase2_model,
                max_tokens=4096,
                system=PHASE2_SYSTEM,
                messages=messages,
            )
            iter_in_tok = response.usage.input_tokens
            iter_out_tok = response.usage.output_tokens
            phase2_in_tok += iter_in_tok
            phase2_out_tok += iter_out_tok
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
        gate1_kind = ""
        if (
            len(vr.results) == 1
            and not vr.results[0].passed
            and vr.results[0].check_type in ("syntax", "validation")
        ):
            gate1_kind = vr.results[0].check_type   # "syntax" or "validation"
        is_syntax_err = gate1_kind == "syntax"
        is_validation_err = gate1_kind == "validation"
        cx_count = sum(1 for r in vr.results if not r.passed and r.counterexample)
        passed = sum(1 for r in vr.results if r.passed)

        if vr.loss == 0:
            status = "pass"
        elif is_syntax_err:
            status = "syntax_error"
        elif is_validation_err:
            status = "validation_error"
        else:
            status = "fail"

        log_entry = IterationLog(
            iteration=iteration,
            loss=vr.loss,
            checks_passed=passed,
            checks_total=checks_total,
            solver_time_s=round(vr.solver_time_s, 3),
            counterexample_count=cx_count,
            # syntax_valid is True iff Gate 1 (parse + type-check) accepted it
            syntax_valid=not (is_syntax_err or is_validation_err),
            status=status,
            input_tokens=iter_in_tok,
            output_tokens=iter_out_tok,
        )
        iteration_log.append(asdict(log_entry))

        # Print status
        if is_syntax_err:
            print(f"  SYNTAX ERROR  solver: {vr.solver_time_s:.2f}s")
        elif is_validation_err:
            print(f"  VALIDATION ERROR  solver: {vr.solver_time_s:.2f}s")
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

        # ── Hash-based oscillation detection ──
        # Track every (hash → iter, failures) pair so we can shout when the
        # model resubmits a byte-identical policy. The failure modes that
        # come back may be from a *different* gate category than last time
        # (e.g. parse vs semantic), which is exactly the cycle Haiku falls
        # into when it removes a `has` guard to satisfy a semantic ceiling.
        cand_hash = hashlib.sha256(candidate_text.encode("utf-8")).hexdigest()
        current_failed = [r.check_name for r in vr.results if not r.passed]
        failure_history.append(set(current_failed))
        repeat_info = None
        if cand_hash in seen_hashes:
            first_iter, first_failed = seen_hashes[cand_hash]
            # Union of failure-mode names across the entire iteration window
            window_union: set[str] = set()
            for fs in failure_history[first_iter - 1 : iteration]:
                window_union |= fs
            repeat_info = {
                "first_iter": first_iter,
                "first_failed": first_failed,
                "current_failed": current_failed,
                "window_union": sorted(window_union),
            }
            print(
                f"  ⚠ OSCILLATION: byte-identical to iter {first_iter}; "
                f"{len(window_union)} unique failure modes seen so far"
            )
        else:
            seen_hashes[cand_hash] = (iteration, list(current_failed))

        # ── Feedback for next iteration ──
        feedback = _format_feedback(
            vr, checks, prev_failed,
            repeat_info=repeat_info,
            candidate_text=candidate_text,
        )
        prev_failed = set(current_failed)
        messages.append({"role": "user", "content": feedback})

        # Trim conversation to avoid context limits: keep first message + last 8
        if len(messages) > 12:
            messages = messages[:1] + messages[-8:]

    phase2_time = time.monotonic() - t2
    total_time = time.monotonic() - t_start
    final_loss = iteration_log[-1]["loss"] if iteration_log else -1

    total_in = phase1_in_tok + phase2_in_tok
    total_out = phase1_out_tok + phase2_out_tok
    cost = (_estimate_cost(phase1_model, phase1_in_tok, phase1_out_tok)
            + _estimate_cost(phase2_model, phase2_in_tok, phase2_out_tok))

    result = ScenarioResult(
        scenario=scenario_name,
        model=phase2_model,
        phase1_model=phase1_model,
        phase2_model=phase2_model,
        converged=(final_loss == 0),
        iterations=len(iteration_log),
        max_iterations=max_iters,
        total_time_s=round(total_time, 2),
        phase1_time_s=round(phase1_time, 2),
        phase2_time_s=round(phase2_time, 2),
        final_loss=final_loss,
        checks_total=checks_total,
        iteration_log=iteration_log,
        phase1_input_tokens=phase1_in_tok,
        phase1_output_tokens=phase1_out_tok,
        phase2_input_tokens=phase2_in_tok,
        phase2_output_tokens=phase2_out_tok,
        total_input_tokens=total_in,
        total_output_tokens=total_out,
        total_tokens=total_in + total_out,
        estimated_cost_usd=round(cost, 4),
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
  python eval_harness.py --scenario experiments/github --no-review
  python eval_harness.py --scenario experiments/github --phase1-model claude-sonnet-4-20250514 --phase2-model claude-haiku-4-5-20251001 --gen-references --no-review
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
        "--model", default=None,
        help=f"LLM model for both phases (convenience shorthand; overrides phase defaults)",
    )
    parser.add_argument(
        "--phase1-model", default=None,
        help=f"LLM model for Phase 1 reference generation (default: {DEFAULT_PHASE1_MODEL}, overrides --model)",
    )
    parser.add_argument(
        "--phase2-model", nargs="+", default=None,
        help=f"LLM model(s) for Phase 2 synthesis; pass multiple to compare (default: {DEFAULT_MODEL}, overrides --model)",
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

    # Resolve models: --phase1-model / --phase2-model override --model
    # Phase 1 defaults to Opus (heavy reasoning), Phase 2 defaults to Sonnet (iterative).
    # --model is a convenience shorthand that overrides both phases.
    base_model = args.model  # may be None
    phase1_model = args.phase1_model or base_model or DEFAULT_PHASE1_MODEL
    phase2_models = args.phase2_model or [base_model or DEFAULT_MODEL]

    # Create run directory
    run_id = args.run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = os.path.join(EVAL_RUNS_DIR, run_id)
    os.makedirs(run_dir, exist_ok=True)

    print("=" * 60)
    print("CEDAR SYNTHESIS ENGINE — EVALUATION HARNESS")
    print("=" * 60)
    print(f"Run ID:     {run_id}")
    print(f"Phase 1:    {phase1_model}")
    print(f"Phase 2:    {', '.join(phase2_models)}")
    print(f"Max iters:  {args.max_iters}")
    print(f"Review:     {'disabled' if args.no_review else 'enabled (human-in-the-loop)'}")
    print(f"Scenarios:  {len(scenarios)}")
    for s in scenarios:
        print(f"  - {os.path.relpath(s, ROOT_DIR)}")
    print(f"Output:     {os.path.relpath(run_dir, ROOT_DIR)}")

    # Run each (scenario, phase2_model) combination
    all_results = []
    for p2_model in phase2_models:
        # When comparing models, namespace run dirs by model
        if len(phase2_models) > 1:
            model_run_dir = os.path.join(run_dir, p2_model.replace("/", "_"))
            os.makedirs(model_run_dir, exist_ok=True)
        else:
            model_run_dir = run_dir

        for scenario_path in scenarios:
            result = run_scenario(
                scenario_path=scenario_path,
                run_dir=model_run_dir,
                phase1_model=phase1_model,
                phase2_model=p2_model,
                max_iters=args.max_iters,
                gen_references=args.gen_references,
                no_review=args.no_review,
            )
            all_results.append(asdict(result))

    # Save summary
    summary = {
        "run_id": run_id,
        "phase1_model": phase1_model,
        "phase2_models": phase2_models,
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

    header = f"{'Scenario':<22} {'Phase 2 Model':<28} {'Result':<8} {'Iters':<7} {'Loss':<5} {'Tokens':<10} {'Cost':<8} {'Time':<7}"
    print(header)
    print("-" * 95)

    for r in all_results:
        if r.get("error"):
            status = "ERROR"
        elif r["converged"]:
            status = "PASS"
        else:
            status = "FAIL"

        model_short = r["phase2_model"].split("/")[-1]
        if len(model_short) > 26:
            model_short = model_short[:24] + ".."

        iters = f"{r['iterations']}/{r['max_iterations']}"
        t = f"{r['total_time_s']:.1f}s"
        tokens = f"{r.get('total_tokens', 0):,}"
        cost = f"${r.get('estimated_cost_usd', 0):.3f}"
        print(f"{r['scenario']:<22} {model_short:<28} {status:<8} {iters:<7} {r['final_loss']:<5} {tokens:<10} {cost:<8} {t:<7}")

    converged = sum(1 for r in all_results if r["converged"])
    total = len(all_results)
    total_cost = sum(r.get("estimated_cost_usd", 0) for r in all_results)
    total_tokens = sum(r.get("total_tokens", 0) for r in all_results)
    print("-" * 95)
    print(f"Converged: {converged}/{total}  |  Total tokens: {total_tokens:,}  |  Total cost: ${total_cost:.3f}")
    print(f"Results:   {os.path.relpath(summary_path, ROOT_DIR)}")

    if any(r.get("error") for r in all_results):
        print("\nErrors:")
        for r in all_results:
            if r.get("error"):
                print(f"  {r['scenario']} ({r['model']}): {r['error']}")

    return 0 if converged == total else 1


if __name__ == "__main__":
    sys.exit(main())
