"""
Cedar Synthesis Engine — Admin Review

Interactive CLI for security administrators to review, approve, and modify
reference policies (ceilings + floors) in natural language before synthesis.

Usage:
    python -m autocedar.harness.review

The configured AutoCedar provider performs optional plain-language
translation. Human approval remains an explicit interactive decision.
"""
import os
import sys
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from autocedar.harness.translator import policy_to_nl, feedback_to_policy

WORKSPACE = os.path.abspath(
    os.environ.get("AUTOCEDAR_WORKSPACE", os.path.join(os.getcwd(), "workspace")),
)
SCHEMA_PATH = os.path.join(WORKSPACE, "schema.cedarschema")
REFS_DIR = os.path.join(WORKSPACE, "references")


def validate_policy(schema_path: str, policy_path: str) -> tuple[bool, str]:
    """Validate a Cedar policy against the schema."""
    try:
        result = subprocess.run(
            ["cedar", "validate", "--schema", schema_path, "--policies", policy_path],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0, (result.stderr.strip() or result.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return False, str(e)


def review_policy(ref_file: str, schema: str) -> None:
    """Review a single reference policy file."""
    ref_path = os.path.join(REFS_DIR, ref_file)
    with open(ref_path) as f:
        policy_text = f.read()

    # Determine policy type from filename
    if ref_file.startswith("ceiling_"):
        policy_type = "CEILING (maximum permissive boundary)"
    elif ref_file.startswith("floor_"):
        policy_type = "FLOOR (minimum required access)"
    else:
        policy_type = "REFERENCE"

    print(f"\n{'─' * 60}")
    print(f"  📄 {ref_file}")
    print(f"  Type: {policy_type}")
    print(f"{'─' * 60}")

    # Show raw Cedar
    print(f"\n  Cedar policy:")
    for line in policy_text.strip().split("\n"):
        print(f"    {line}")

    # Translate to NL
    print(f"\n  ⏳ Translating to plain language...")
    try:
        nl = policy_to_nl(policy_text, schema)
        print(f"\n  Plain language summary:")
        for line in nl.strip().split("\n"):
            print(f"    {line}")
    except Exception as e:
        print(f"\n  ⚠ Translation failed: {e}")
        nl = None

    # Feedback loop
    while True:
        print(f"\n  [Enter feedback to modify, or press Enter to approve]")
        try:
            feedback = input("  > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  ✗ Skipped")
            return

        if not feedback:
            print(f"  ✓ Approved")
            return

        # Generate updated policy
        print(f"\n  ⏳ Generating updated policy...")
        try:
            updated = feedback_to_policy(feedback, policy_text, schema)
        except Exception as e:
            print(f"  ⚠ Update failed: {e}")
            continue

        print(f"\n  Proposed update:")
        for line in updated.strip().split("\n"):
            print(f"    {line}")

        # Validate syntax before applying
        tmp_path = ref_path + ".tmp"
        with open(tmp_path, "w") as f:
            f.write(updated)

        is_valid, msg = validate_policy(SCHEMA_PATH, tmp_path)
        os.remove(tmp_path)

        if not is_valid:
            print(f"\n  ⚠ Updated policy has syntax errors:")
            print(f"    {msg}")
            print(f"  Please provide different feedback.")
            continue

        print(f"\n  ✓ Syntax valid")

        try:
            confirm = input("  Apply this change? [y/N] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n  ✗ Skipped")
            return

        if confirm == "y":
            with open(ref_path, "w") as f:
                f.write(updated)
            print(f"  ✓ Updated {ref_file}")

            # Show NL summary of the updated policy
            print(f"\n  ⏳ Translating updated policy...")
            try:
                nl = policy_to_nl(updated, schema)
                print(f"\n  Updated summary:")
                for line in nl.strip().split("\n"):
                    print(f"    {line}")
            except Exception:
                pass
            return
        else:
            print(f"  ✗ Change rejected — you can provide new feedback")


def main():
    print("=" * 60)
    print("  CEDAR SYNTHESIS ENGINE — ADMIN REVIEW")
    print("=" * 60)

    # Read schema
    with open(SCHEMA_PATH) as f:
        schema = f.read()

    print(f"\n  Schema: {SCHEMA_PATH}")

    # Discover reference policies
    ref_files = sorted(f for f in os.listdir(REFS_DIR) if f.endswith(".cedar"))

    if not ref_files:
        print("\n  No reference policies found in workspace/references/")
        sys.exit(1)

    print(f"  Found {len(ref_files)} reference policies to review:")
    for f in ref_files:
        print(f"    • {f}")

    # Review each
    for ref_file in ref_files:
        review_policy(ref_file, schema)

    # Summary
    print(f"\n{'=' * 60}")
    print("  REVIEW COMPLETE")
    print(f"{'=' * 60}")
    print("  All reference policies have been reviewed.")
    print("  Run the orchestrator to verify candidate policies:")
    print("    CVC5=~/.local/bin/cvc5 python orchestrator.py")
    print()


if __name__ == "__main__":
    main()
