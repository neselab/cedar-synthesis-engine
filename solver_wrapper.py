"""
Solver Wrapper for the Cedar Synthesis Engine.

Uses Cedar CLI v4.10+ with `symcc` subcommand for formal verification.
The solver uses CVC5 under the hood — no @domain annotations needed.
"""
import json
import os
import subprocess
from dataclasses import dataclass


CVC5_PATH = os.environ.get("CVC5", os.path.expanduser("~/.local/bin/cvc5"))


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class CheckResult:
    """Result of a single verification check."""
    check_name: str
    check_type: str          # "implies", "always-denies", "never-errors"
    description: str
    passed: bool
    counterexample: str      # Empty if passed


@dataclass
class VerificationResult:
    """Aggregated result of all checks."""
    loss: int                        # Number of failed checks
    results: list[CheckResult]       # Individual check results
    solver_time_s: float = 0.0       # Wall-clock time for all solver calls

    @property
    def passed(self) -> bool:
        return self.loss == 0


# ---------------------------------------------------------------------------
# Gate 1: Syntax check (unchanged)
# ---------------------------------------------------------------------------

def run_syntax_check(schema_path: str, policy_path: str) -> tuple[bool, str]:
    """Run `cedar validate` on the given policy against the schema."""
    try:
        result = subprocess.run(
            ["cedar", "validate", "--schema", schema_path, "--policies", policy_path],
            capture_output=True,
            text=True,
            timeout=10,
        )
        is_valid = result.returncode == 0
        error_msg = ""
        if not is_valid:
            error_msg = (result.stderr.strip() or result.stdout.strip())
        return is_valid, error_msg
    except subprocess.TimeoutExpired:
        return False, "Cedar validate timed out."
    except FileNotFoundError:
        return False, "Cedar CLI not found. Install with: cargo install cedar-policy-cli"


# ---------------------------------------------------------------------------
# Gate 2: Symcc verification
# ---------------------------------------------------------------------------

def _run_symcc(
    schema_path: str,
    principal_type: str,
    action: str,
    resource_type: str,
    subcommand: str,
    extra_args: list[str],
) -> tuple[bool, str]:
    """
    Run a single `cedar symcc` check.
    Returns (passed, output_text).
    """
    cmd = [
        "cedar", "symcc",
        "--cvc5-path", CVC5_PATH,
        "--principal-type", principal_type,
        "--action", action,
        "--resource-type", resource_type,
        "--schema", schema_path,
        "--counterexample",
        subcommand,
    ] + extra_args

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = result.stdout.strip() or result.stderr.strip()
        passed = "VERIFIED" in output
        return passed, output
    except subprocess.TimeoutExpired:
        return False, "CVC5 solver timed out (30s limit)."
    except FileNotFoundError:
        return False, f"CVC5 not found at {CVC5_PATH}. Set CVC5 env var."


def run_implies_check(
    schema_path: str,
    candidate_path: str,
    reference_path: str,
    principal_type: str,
    action: str,
    resource_type: str,
    check_name: str,
    description: str,
) -> CheckResult:
    """
    Check: candidate ≤ reference (candidate is no more permissive).
    Uses `cedar symcc implies --policies1 <candidate> --policies2 <reference>`.
    """
    passed, output = _run_symcc(
        schema_path, principal_type, action, resource_type,
        "implies",
        ["--policies1", candidate_path, "--policies2", reference_path],
    )
    return CheckResult(
        check_name=check_name,
        check_type="implies",
        description=description,
        passed=passed,
        counterexample="" if passed else output,
    )


def run_always_denies_check(
    schema_path: str,
    candidate_path: str,
    principal_type: str,
    action: str,
    resource_type: str,
    check_name: str,
    description: str,
    expect_denies: bool = True,
) -> CheckResult:
    """
    Check: does the policy always deny for this request environment?
    For liveness: we want always-denies to be FALSE (expect_denies=False).
    """
    passed_raw, output = _run_symcc(
        schema_path, principal_type, action, resource_type,
        "always-denies",
        ["--policies", candidate_path],
    )
    # If expect_denies=False (liveness), we want the check to FAIL (not always deny)
    if expect_denies:
        passed = passed_raw
    else:
        passed = not passed_raw  # We WANT it to not always deny

    return CheckResult(
        check_name=check_name,
        check_type="always-denies (liveness)" if not expect_denies else "always-denies",
        description=description,
        passed=passed,
        counterexample="" if passed else (
            "LIVENESS VIOLATION: Policy always denies this action. "
            "It must allow at least one scenario."
            if not expect_denies else output
        ),
    )


def run_never_errors_check(
    schema_path: str,
    candidate_path: str,
    principal_type: str,
    action: str,
    resource_type: str,
) -> CheckResult:
    """Check: policy never produces runtime errors."""
    passed, output = _run_symcc(
        schema_path, principal_type, action, resource_type,
        "never-errors",
        ["--policies", candidate_path],
    )
    return CheckResult(
        check_name="no_runtime_errors",
        check_type="never-errors",
        description="Policy must not produce runtime errors for any input",
        passed=passed,
        counterexample="" if passed else output,
    )
