"""
Cedar Synthesis Engine — Orchestrator

Evaluator script the coding agent runs.
Reads candidate policy, validates syntax, and runs all verification checks
from the verification plan using `cedar symcc`.

Usage:
    CVC5=~/.local/bin/cvc5 python orchestrator.py
    CVC5=~/.local/bin/cvc5 python orchestrator.py --translate   # NL output
"""
import argparse
import importlib.util
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from solver_wrapper import (
    CheckResult,
    VerificationResult,
    run_syntax_check,
    run_implies_check,
    run_always_denies_check,
    run_never_errors_check,
)

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_WORKSPACE = os.path.join(ROOT_DIR, "workspace")


# ---------------------------------------------------------------------------
# Reusable verification runner
# ---------------------------------------------------------------------------

def load_checks(workspace: str) -> list[dict]:
    """Load verification checks from workspace/verification_plan.py."""
    vp_path = os.path.join(workspace, "verification_plan.py")
    spec = importlib.util.spec_from_file_location("verification_plan", vp_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.get_checks()


def run_verification(workspace: str) -> VerificationResult:
    """
    Run all verification gates on workspace/candidate.cedar.

    Returns a VerificationResult with per-check results, total loss,
    and wall-clock solver time.
    """
    schema_path = os.path.join(workspace, "schema.cedarschema")
    candidate_path = os.path.join(workspace, "candidate.cedar")

    # Gate 1: syntax
    is_valid, error_msg = run_syntax_check(schema_path, candidate_path)
    if not is_valid:
        return VerificationResult(
            loss=1,
            results=[CheckResult(
                check_name="syntax",
                check_type="syntax",
                description="Cedar syntax validation",
                passed=False,
                counterexample=error_msg,
            )],
        )

    # Gate 2: verification plan
    checks = load_checks(workspace)
    results = []
    t0 = time.monotonic()

    for check in checks:
        ctype = check["type"]

        if ctype == "implies":
            result = run_implies_check(
                schema_path=schema_path,
                candidate_path=candidate_path,
                reference_path=check["reference_path"],
                principal_type=check["principal_type"],
                action=check["action"],
                resource_type=check["resource_type"],
                check_name=check["name"],
                description=check["description"],
            )
        elif ctype == "always-denies-liveness":
            result = run_always_denies_check(
                schema_path=schema_path,
                candidate_path=candidate_path,
                principal_type=check["principal_type"],
                action=check["action"],
                resource_type=check["resource_type"],
                check_name=check["name"],
                description=check["description"],
                expect_denies=False,  # Liveness: we want NOT always-denies
            )
        elif ctype == "never-errors":
            result = run_never_errors_check(
                schema_path=schema_path,
                candidate_path=candidate_path,
                principal_type=check["principal_type"],
                action=check["action"],
                resource_type=check["resource_type"],
            )
        elif ctype == "floor":
            # Reverse-implies: floor ≤ candidate
            result = run_implies_check(
                schema_path=schema_path,
                candidate_path=check["floor_path"],    # floor is policies1
                reference_path=candidate_path,          # candidate is policies2
                principal_type=check["principal_type"],
                action=check["action"],
                resource_type=check["resource_type"],
                check_name=check["name"],
                description=check["description"],
            )
        else:
            continue

        results.append(result)

    solver_time = time.monotonic() - t0
    loss = sum(1 for r in results if not r.passed)
    return VerificationResult(loss=loss, results=results, solver_time_s=solver_time)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Cedar Synthesis Engine Evaluator")
    parser.add_argument(
        "--translate", action="store_true",
        help="Enable NL translation of counterexamples (requires ANTHROPIC_API_KEY)",
    )
    parser.add_argument(
        "--workspace", type=str, default=DEFAULT_WORKSPACE,
        help="Path to workspace directory (default: ./workspace)",
    )
    args = parser.parse_args()

    workspace = os.path.abspath(args.workspace)
    candidate_path = os.path.join(workspace, "candidate.cedar")
    policy_store_path = os.path.join(workspace, "policy_store.cedar")
    schema_path = os.path.join(workspace, "schema.cedarschema")

    translate = args.translate
    if translate:
        try:
            from translator import counterexample_to_nl, policy_to_nl
        except ImportError:
            print("WARNING: translator module not found, disabling --translate")
            translate = False
        if not os.environ.get("ANTHROPIC_API_KEY"):
            print("WARNING: ANTHROPIC_API_KEY not set, disabling --translate")
            translate = False

    print("=" * 60)
    print("CEDAR SYNTHESIS ENGINE — EVALUATOR")
    print("=" * 60)

    if not os.path.exists(candidate_path):
        print(f"\nERROR: {candidate_path} not found.")
        print("Write your candidate policy to candidate.cedar first.")
        sys.exit(1)

    # Run verification
    vr = run_verification(workspace)

    # Check for syntax gate failure
    if vr.results and vr.results[0].check_type == "syntax" and not vr.results[0].passed:
        print("\n--- Gate 1: Syntax Check ---")
        print(f"syntax:    FAIL")
        print(f"error:     {vr.results[0].counterexample}")
        print(f"\nloss:      SYNTAX_ERROR")
        sys.exit(1)

    print("\n--- Gate 1: Syntax Check ---")
    print("syntax:    PASS")
    print("\n--- Gate 2: Verification Plan ---")

    for r in vr.results:
        status = "✓ PASS" if r.passed else "✗ FAIL"
        print(f"  {r.check_name}: {status}")

    # ----- Results -----
    print(f"\nloss:      {vr.loss}")

    if vr.loss == 0:
        print("\nRESULT: ALL CHECKS PASSED ✓")
        print("The candidate policy is formally verified.")

        # Append verified candidate to policy store
        with open(candidate_path) as f:
            verified = f.read()
        with open(policy_store_path, "a") as f:
            f.write(f"\n// --- Verified and appended ---\n{verified}")
        print(f"Policy appended to {os.path.basename(policy_store_path)}.")
    else:
        print(f"\nRESULT: {vr.loss} CHECK(S) FAILED ✗")
        print("\nFailures:")
        for i, r in enumerate(vr.results, 1):
            if not r.passed:
                print(f"\n  failure_{i}:")
                print(f"    check:       {r.check_name} ({r.check_type})")
                print(f"    description: {r.description}")
                print(f"    details:     {r.counterexample}")
                if translate:
                    try:
                        nl = counterexample_to_nl(
                            r.counterexample, r.check_name, r.description
                        )
                        print(f"    plain_lang:  {nl}")
                    except Exception as e:
                        print(f"    plain_lang:  (translation failed: {e})")

    if vr.loss == 0 and translate:
        try:
            with open(candidate_path) as f:
                candidate_text = f.read()
            with open(schema_path) as f:
                schema_text = f.read()
            print("\n--- Verified Policy Summary ---")
            summary = policy_to_nl(candidate_text, schema_text)
            print(summary)
        except Exception as e:
            print(f"\n(Policy summary translation failed: {e})")

    print("\n" + "=" * 60)
    return vr.loss


if __name__ == "__main__":
    loss = main()
    sys.exit(0 if loss == 0 else 1)
