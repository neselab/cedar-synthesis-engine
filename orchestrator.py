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
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from solver_wrapper import (
    run_syntax_check,
    run_implies_check,
    run_always_denies_check,
    run_never_errors_check,
)

WORKSPACE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "workspace")
SCHEMA_PATH = os.path.join(WORKSPACE, "schema.cedarschema")
CANDIDATE_PATH = os.path.join(WORKSPACE, "candidate.cedar")
POLICY_STORE_PATH = os.path.join(WORKSPACE, "policy_store.cedar")


def main():
    parser = argparse.ArgumentParser(description="Cedar Synthesis Engine Evaluator")
    parser.add_argument(
        "--translate", action="store_true",
        help="Enable NL translation of counterexamples (requires ANTHROPIC_API_KEY)",
    )
    args = parser.parse_args()

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

    if not os.path.exists(CANDIDATE_PATH):
        print("\nERROR: workspace/candidate.cedar not found.")
        print("Write your candidate policy to workspace/candidate.cedar first.")
        sys.exit(1)

    # ----- Gate 1: Syntax Check -----
    print("\n--- Gate 1: Syntax Check ---")
    is_valid, error_msg = run_syntax_check(SCHEMA_PATH, CANDIDATE_PATH)
    if not is_valid:
        print(f"syntax:    FAIL")
        print(f"error:     {error_msg}")
        print(f"\nloss:      SYNTAX_ERROR")
        sys.exit(1)
    print("syntax:    PASS")

    # ----- Gate 2: Verification Plan -----
    print("\n--- Gate 2: Verification Plan ---")

    from workspace.verification_plan import get_checks
    checks = get_checks()

    results = []
    for check in checks:
        ctype = check["type"]

        if ctype == "implies":
            result = run_implies_check(
                schema_path=SCHEMA_PATH,
                candidate_path=CANDIDATE_PATH,
                reference_path=check["reference_path"],
                principal_type=check["principal_type"],
                action=check["action"],
                resource_type=check["resource_type"],
                check_name=check["name"],
                description=check["description"],
            )
        elif ctype == "always-denies-liveness":
            result = run_always_denies_check(
                schema_path=SCHEMA_PATH,
                candidate_path=CANDIDATE_PATH,
                principal_type=check["principal_type"],
                action=check["action"],
                resource_type=check["resource_type"],
                check_name=check["name"],
                description=check["description"],
                expect_denies=False,  # Liveness: we want NOT always-denies
            )
        elif ctype == "never-errors":
            result = run_never_errors_check(
                schema_path=SCHEMA_PATH,
                candidate_path=CANDIDATE_PATH,
                principal_type=check["principal_type"],
                action=check["action"],
                resource_type=check["resource_type"],
            )
        elif ctype == "floor":
            # Reverse-implies: floor ≤ candidate
            # Verifies candidate allows at least what the floor demands
            result = run_implies_check(
                schema_path=SCHEMA_PATH,
                candidate_path=check["floor_path"],    # floor is policies1
                reference_path=CANDIDATE_PATH,          # candidate is policies2
                principal_type=check["principal_type"],
                action=check["action"],
                resource_type=check["resource_type"],
                check_name=check["name"],
                description=check["description"],
            )
        else:
            print(f"  WARNING: Unknown check type '{ctype}', skipping")
            continue

        results.append(result)
        status = "✓ PASS" if result.passed else "✗ FAIL"
        print(f"  {result.check_name}: {status}")

    # ----- Results -----
    loss = sum(1 for r in results if not r.passed)
    print(f"\nloss:      {loss}")

    if loss == 0:
        print("\nRESULT: ALL CHECKS PASSED ✓")
        print("The candidate policy is formally verified.")

        # Append verified candidate to policy store
        with open(CANDIDATE_PATH) as f:
            verified = f.read()
        with open(POLICY_STORE_PATH, "a") as f:
            f.write(f"\n// --- Verified and appended ---\n{verified}")
        print(f"Policy appended to {os.path.basename(POLICY_STORE_PATH)}.")
    else:
        print(f"\nRESULT: {loss} CHECK(S) FAILED ✗")
        print("\nFailures:")
        for i, r in enumerate(results, 1):
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

    if loss == 0 and translate:
        try:
            with open(CANDIDATE_PATH) as f:
                candidate_text = f.read()
            with open(SCHEMA_PATH) as f:
                schema_text = f.read()
            print("\n--- Verified Policy Summary ---")
            summary = policy_to_nl(candidate_text, schema_text)
            print(summary)
        except Exception as e:
            print(f"\n(Policy summary translation failed: {e})")

    print("\n" + "=" * 60)
    return loss


if __name__ == "__main__":
    loss = main()
    sys.exit(0 if loss == 0 else 1)
