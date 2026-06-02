"""Packaged access to the v1 Cedar CEGIS harness.

The repository still keeps root-level script entry points for backwards
compatibility. This package namespace is the import surface used by the
installable ``autocedar`` CLI.
"""

from autocedar.harness.orchestrator import load_checks, run_verification
from autocedar.harness.solver_wrapper import (
    CheckResult,
    VerificationResult,
    run_always_denies_check,
    run_implies_check,
    run_never_errors_check,
    run_syntax_check,
)

__all__ = [
    "CheckResult",
    "VerificationResult",
    "load_checks",
    "run_always_denies_check",
    "run_implies_check",
    "run_never_errors_check",
    "run_syntax_check",
    "run_verification",
]
