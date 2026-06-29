"""Symbolic verification + adversarial-example generation for Stage 2 atoms.

The symbolic checks per atom are:

1. Satisfiability — there exists a request the encoding permits/denies.
2. Joint consistency — atom is jointly satisfiable with previously-
   approved atoms (pairwise floor-implies-ceiling on same action).
3. Type correctness — ``cedar validate`` against the composed schema.
4. Sugar-specific universal claims — structural sanity checks for
   sugar atoms such as disjointness and rate limits.
5. Identity consistency — schema-valid entity equality does not compare
   parallel account/role identities as if they were the same Cedar entity.

Per §1.4, these earn the **formal-consistency** badge. They do NOT
prove the encoding is a faithful translation of the prose; that is
human judgment exercised by the user during atom review.

The adversarial-example pipeline (§4.4) generates examples that
distinguish the chosen encoding from plausible alternative readings:

- ``propose_alternatives`` — injectable LLM-driven alternative proposal.
  Offline tests can pass alternatives directly or use the empty default.
- ``find_distinguishing_request`` — runs ``cedar symcc implies`` in
  both directions and returns a counterexample (a request) where the
  chosen and alternative encodings disagree.
- ``generate_adversarial_examples`` — orchestrates the above.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Literal, Optional

from autocedar.atoms import (
    AlternativeEncoding,
    Example,
    PropertyAtom,
)
from autocedar.identity_model import find_identity_issues, format_identity_issues

CEDAR_PATH = os.environ.get("CEDAR", os.path.expanduser("~/.cargo/bin/cedar"))
CVC5_PATH = (
    os.environ.get("CVC5")
    or shutil.which("cvc5")
    or os.path.expanduser("~/.local/bin/cvc5")
)


# ---------------------------------------------------------------------------
# Result objects.
# ---------------------------------------------------------------------------

@dataclass
class SymbolicCheck:
    """Result of one of the four atom-level symcc checks (§4.1)."""

    name: str  # "satisfiable" | "joint-consistency-with-<atom>" | "type-correct" | "sugar-universal"
    passed: bool
    detail: str = ""


SymccOutcome = Literal["verified", "counterexample", "setup_error", "timeout", "unknown"]


@dataclass
class SymccSignal:
    """Structured SymCC signal for verifier-guided feedback.

    Older code consumed ``(passed, output)`` pairs. This object keeps that
    compatibility while preserving the richer information needed by repair
    prompts and review UI: the exact command shape, formal outcome, setup/tool
    classification, and compact policy excerpts.
    """

    subcommand: str
    command: list[str]
    passed: bool
    outcome: SymccOutcome
    raw_output: str
    tool_error: bool = False
    counterexample: str = ""
    candidate_excerpt: str = ""
    reference_excerpt: str = ""

    def compact_detail(self, limit: int = 1200) -> str:
        parts = [
            f"symcc {self.subcommand}: {self.outcome}",
            "command: " + " ".join(self.command),
        ]
        if self.candidate_excerpt:
            parts.append("candidate/reference 1:\n" + self.candidate_excerpt.strip())
        if self.reference_excerpt:
            parts.append("reference/policy 2:\n" + self.reference_excerpt.strip())
        if self.counterexample:
            parts.append("counterexample:\n" + self.counterexample.strip())
        elif self.raw_output:
            parts.append("output:\n" + self.raw_output.strip())
        detail = "\n".join(parts)
        return detail if len(detail) <= limit else detail[: limit - 3].rstrip() + "..."


@dataclass
class SymbolicVerificationResult:
    """Aggregated result of all four checks for one atom."""

    atom_name: str
    checks: list[SymbolicCheck] = field(default_factory=list)

    @property
    def all_passed(self) -> bool:
        return all(c.passed for c in self.checks)

    def log_lines(self) -> list[str]:
        """Compact entries to populate ``atom.symbolic_verification_log``."""
        return [
            f"{c.name}: {'ok' if c.passed else 'FAILED'}"
            + (f" ({c.detail})" if c.detail else "")
            for c in self.checks
        ]


# ---------------------------------------------------------------------------
# Subprocess helpers for cedar / symcc.
# ---------------------------------------------------------------------------

def _action_literal(action: str) -> str:
    """Render an action name as the ``Action::"..."`` literal symcc expects."""
    return action if action.startswith("Action::") else f'Action::"{action}"'


def _run_cedar_validate(
    schema_path: str,
    policy_text: str,
    workdir: Path,
    label: str = "atom",
) -> tuple[bool, str]:
    """Run ``cedar validate`` on a Cedar policy text against a schema.

    Returns ``(passed, error_text)``.
    """
    policy_path = workdir / f"{label}.cedar"
    policy_path.write_text(policy_text)
    try:
        result = subprocess.run(
            [CEDAR_PATH, "validate", "--schema", schema_path, "--policies", str(policy_path)],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except subprocess.TimeoutExpired:
        return False, "cedar validate timed out"
    except FileNotFoundError:
        return False, f"cedar binary not found at {CEDAR_PATH}"
    if result.returncode == 0:
        return True, ""
    detail = (result.stderr.strip() or result.stdout.strip())[:300]
    return False, f"cedar validate rc={result.returncode}: {detail}"


def _run_symcc(
    schema_path: str,
    principal_type: str,
    action: str,
    resource_type: str,
    subcommand: str,
    extra_args: list[str],
    timeout_s: int = 30,
) -> tuple[bool, str]:
    """Run ``cedar symcc <subcommand>`` and parse the VERIFIED/COUNTEREXAMPLE.

    ``passed`` is True iff the output contains "VERIFIED". The full
    output (which contains the counterexample for failed checks) is
    returned for downstream callers.
    """
    signal = _run_symcc_signal(
        schema_path=schema_path,
        principal_type=principal_type,
        action=action,
        resource_type=resource_type,
        subcommand=subcommand,
        extra_args=extra_args,
        timeout_s=timeout_s,
    )
    return signal.passed, signal.raw_output


def _run_symcc_signal(
    schema_path: str,
    principal_type: str,
    action: str,
    resource_type: str,
    subcommand: str,
    extra_args: list[str],
    timeout_s: int = 30,
    candidate_excerpt: str = "",
    reference_excerpt: str = "",
) -> SymccSignal:
    """Run ``cedar symcc`` and preserve a structured verifier signal."""
    command_args = _with_plain_error_format(extra_args)
    cmd_with_cvc5 = [
        CEDAR_PATH,
        "symcc",
        "--cvc5-path",
        CVC5_PATH,
        "--principal-type",
        principal_type,
        "--action",
        _action_literal(action),
        "--resource-type",
        resource_type,
        "--schema",
        schema_path,
        "--counterexample",
        subcommand,
    ] + command_args
    cmd_without_cvc5 = [
        CEDAR_PATH,
        "symcc",
        "--principal-type",
        principal_type,
        "--action",
        _action_literal(action),
        "--resource-type",
        resource_type,
        "--schema",
        schema_path,
        "--counterexample",
        subcommand,
    ] + command_args
    final_cmd = cmd_with_cvc5
    try:
        result = _run_symcc_command(cmd_with_cvc5, timeout_s)
        output = _subprocess_output(result)
        if _rejects_cvc5_path(output):
            final_cmd = cmd_without_cvc5
            result = _run_symcc_command(cmd_without_cvc5, timeout_s)
    except subprocess.TimeoutExpired:
        return SymccSignal(
            subcommand=subcommand,
            command=final_cmd,
            passed=False,
            outcome="timeout",
            raw_output="symcc timed out",
            tool_error=True,
            candidate_excerpt=candidate_excerpt,
            reference_excerpt=reference_excerpt,
        )
    except FileNotFoundError:
        return SymccSignal(
            subcommand=subcommand,
            command=final_cmd,
            passed=False,
            outcome="setup_error",
            raw_output=f"cedar binary not found at {CEDAR_PATH}",
            tool_error=True,
            candidate_excerpt=candidate_excerpt,
            reference_excerpt=reference_excerpt,
        )
    output = _subprocess_output(result)
    if _is_symcc_tool_error(output, result.returncode):
        return SymccSignal(
            subcommand=subcommand,
            command=final_cmd,
            passed=False,
            outcome="setup_error",
            raw_output=_symcc_tool_error_message(output),
            tool_error=True,
            candidate_excerpt=candidate_excerpt,
            reference_excerpt=reference_excerpt,
        )
    passed = "VERIFIED" in output
    return SymccSignal(
        subcommand=subcommand,
        command=final_cmd,
        passed=passed,
        outcome="verified" if passed else ("counterexample" if _has_symcc_formal_result(output) else "unknown"),
        raw_output=output,
        tool_error=False,
        counterexample="" if passed else _summarize_counterexample(output),
        candidate_excerpt=candidate_excerpt,
        reference_excerpt=reference_excerpt,
    )


def _with_plain_error_format(extra_args: list[str]) -> list[str]:
    """Prefer machine-stable SymCC diagnostics without changing callers."""
    if "--error-format" in extra_args or "-f" in extra_args:
        return extra_args
    return extra_args + ["--error-format", "plain"]


def _run_symcc_command(cmd: list[str], timeout_s: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout_s,
    )


def _subprocess_output(result: subprocess.CompletedProcess[str]) -> str:
    return (result.stdout.strip() + "\n" + result.stderr.strip()).strip()


def _rejects_cvc5_path(output: str) -> bool:
    return "unexpected argument '--cvc5-path'" in output


def _rejects_required_symcc_arg(output: str) -> bool:
    required_args = ("--principal-type", "--action", "--resource-type", "--schema")
    return any(f"unexpected argument '{arg}'" in output for arg in required_args)


def _is_symcc_tool_error(output: str, returncode: int | None = None) -> bool:
    return (
        "Cedar symcc setup error:" in output
        or _is_symcc_interface_error(output)
        or _is_cvc5_tool_error(output)
        or (returncode not in (None, 0) and not _has_symcc_formal_result(output))
    )


def _is_symcc_interface_error(output: str) -> bool:
    return (
        _rejects_required_symcc_arg(output)
        or "not built with `analyze` experimental feature enabled" in output
        or "built without the `analyze` feature enabled" in output
    )


def _has_symcc_formal_result(output: str) -> bool:
    formal_markers = (
        "VERIFIED",
        "DOES NOT HOLD",
        "Counterexample",
        "counterexample",
        "No counterexample found",
    )
    return any(marker in output for marker in formal_markers)


def _is_cvc5_tool_error(output: str) -> bool:
    return (
        "CVC5 solver not found or failed to start" in output
        or "CVC5 solver was not found" in output
        or ("failed to start" in output and "CVC5" in output)
    )


def _symcc_tool_error_message(output: str) -> str:
    compact = " ".join(output.split())
    if len(compact) > 600:
        compact = compact[:597].rstrip() + "..."
    if _is_cvc5_tool_error(output):
        return (
            "Cedar symcc setup error: CVC5 solver was not found or could "
            "not start. Install CVC5 and ensure `cvc5 --version` works, "
            "or set `CVC5=/path/to/cvc5`. Run `uv run autocedar doctor` "
            "for a full setup diagnosis. Raw cedar output: "
            f"{compact}"
        )
    if not _is_symcc_interface_error(output):
        return (
            "Cedar symcc setup error: Cedar symcc exited before producing "
            "a formal verification result. This is a verifier/tooling "
            "failure, not a policy counterexample. Check the Cedar and CVC5 "
            "installations, then rerun `uv run autocedar doctor`. Raw cedar output: "
            f"{compact}"
        )
    return (
        "Cedar symcc setup error: this Cedar CLI does not expose the SymCC "
        "analysis interface AutoCedar needs (--principal-type, --action, "
        "--resource-type, --schema). It is usually cedar-policy-cli installed "
        "without the `analyze` feature. Reinstall with: "
        "`cargo install cedar-policy-cli --locked --features analyze`, or set "
        "`CEDAR` to a compatible cedar binary. Run `uv run autocedar doctor` "
        "for a full setup diagnosis. Raw cedar output: "
        f"{compact}"
    )


def _principal_resource(atom: PropertyAtom) -> tuple[str, str]:
    """Extract (principal_type, resource_type) for an atom's symcc query.

    Falls back to first listed type per side; if either is empty, an
    error is raised because symcc requires both.
    """
    if not atom.principal_types:
        raise ValueError(f"atom {atom.name!r} has no principal_types")
    if not atom.resource_types:
        raise ValueError(f"atom {atom.name!r} has no resource_types")
    return atom.principal_types[0], atom.resource_types[0]


# ---------------------------------------------------------------------------
# The four symcc checks (§4.1).
# ---------------------------------------------------------------------------

def _check_type_correctness(
    atom: PropertyAtom,
    schema_path: str,
    workdir: Path,
) -> SymbolicCheck:
    """Check 3: cedar validate against the composed schema."""
    ok, detail = _run_cedar_validate(
        schema_path, atom.reference_cedar, workdir, label=f"{atom.name}_validate",
    )
    return SymbolicCheck(name="type-correct", passed=ok, detail=detail)


def _check_identity_consistency(
    atom: PropertyAtom,
    schema_path: str,
) -> SymbolicCheck:
    """Catch schema-valid cross-type principal equality."""

    if atom.constraint_type == "liveness" and not atom.reference_cedar:
        return SymbolicCheck(
            name="identity-consistency",
            passed=True,
            detail="liveness atom has no reference encoding",
        )
    issues = find_identity_issues(atom, Path(schema_path).read_text())
    if not issues:
        return SymbolicCheck(name="identity-consistency", passed=True)
    return SymbolicCheck(
        name="identity-consistency",
        passed=False,
        detail=format_identity_issues(issues),
    )


def _check_satisfiability(
    atom: PropertyAtom,
    schema_path: str,
    workdir: Path,
) -> SymbolicCheck:
    """Check 1: the encoding is not vacuous (i.e. not always-denies)."""
    if atom.constraint_type == "liveness" and not atom.reference_cedar:
        # Liveness atoms have no reference encoding to verify.
        return SymbolicCheck(
            name="satisfiable",
            passed=True,
            detail="liveness atom has no reference encoding",
        )
    principal_type, resource_type = _principal_resource(atom)
    policy_path = workdir / f"{atom.name}_sat.cedar"
    policy_path.write_text(atom.reference_cedar)
    always_denies, output = _run_symcc(
        schema_path,
        principal_type,
        atom.action,
        resource_type,
        "always-denies",
        ["--policies", str(policy_path)],
    )
    if _is_symcc_tool_error(output):
        return SymbolicCheck(
            name="satisfiable",
            passed=False,
            detail=output,
        )
    if always_denies:
        return SymbolicCheck(
            name="satisfiable",
            passed=False,
            detail="encoding is vacuous (always denies)",
        )
    return SymbolicCheck(name="satisfiable", passed=True)


def _check_never_errors(
    atom: PropertyAtom,
    schema_path: str,
    workdir: Path,
) -> SymbolicCheck:
    """The atom reference should never raise runtime Cedar errors."""
    if atom.constraint_type == "liveness" and not atom.reference_cedar:
        return SymbolicCheck(
            name="never-errors",
            passed=True,
            detail="liveness atom has no reference encoding",
        )
    principal_type, resource_type = _principal_resource(atom)
    policy_path = workdir / f"{atom.name}_never_errors.cedar"
    policy_path.write_text(atom.reference_cedar)
    signal = _run_symcc_signal(
        schema_path,
        principal_type,
        atom.action,
        resource_type,
        "never-errors",
        ["--policies", str(policy_path)],
        candidate_excerpt=atom.reference_cedar,
    )
    if signal.tool_error:
        return SymbolicCheck(name="never-errors", passed=False, detail=signal.raw_output)
    return SymbolicCheck(
        name="never-errors",
        passed=signal.passed,
        detail="" if signal.passed else signal.compact_detail(),
    )


def _check_match_shape(
    atom: PropertyAtom,
    schema_path: str,
    workdir: Path,
) -> list[SymbolicCheck]:
    """Use individual-policy match checks to flag vacuity and broadness."""
    if atom.constraint_type == "liveness" and not atom.reference_cedar:
        return [
            SymbolicCheck(
                name="match-vacuity",
                passed=True,
                detail="liveness atom has no reference encoding",
            ),
            SymbolicCheck(
                name="match-broadness",
                passed=True,
                detail="liveness atom has no reference encoding",
            ),
        ]
    principal_type, resource_type = _principal_resource(atom)
    policy_path = workdir / f"{atom.name}_match_shape.cedar"
    policy_path.write_text(atom.reference_cedar)

    never_matches = _run_symcc_signal(
        schema_path,
        principal_type,
        atom.action,
        resource_type,
        "never-matches",
        ["--policies", str(policy_path)],
        candidate_excerpt=atom.reference_cedar,
    )
    if never_matches.tool_error:
        return [SymbolicCheck(name="match-vacuity", passed=False, detail=never_matches.raw_output)]
    checks = [
        SymbolicCheck(
            name="match-vacuity",
            passed=not never_matches.passed,
            detail=(
                "individual policy never matches any well-formed request"
                if never_matches.passed
                else "policy match condition is reachable"
            ),
        ),
    ]

    always_matches = _run_symcc_signal(
        schema_path,
        principal_type,
        atom.action,
        resource_type,
        "always-matches",
        ["--policies", str(policy_path)],
        candidate_excerpt=atom.reference_cedar,
    )
    if always_matches.tool_error:
        checks.append(SymbolicCheck(name="match-broadness", passed=False, detail=always_matches.raw_output))
    elif always_matches.passed:
        checks.append(
            SymbolicCheck(
                name="match-broadness",
                passed=True,
                detail="WARNING: individual policy matches every well-formed request in this typed action space",
            ),
        )
    else:
        checks.append(
            SymbolicCheck(
                name="match-broadness",
                passed=True,
                detail="not universal",
            ),
        )
    return checks


def _check_joint_consistency(
    atom: PropertyAtom,
    prior_atoms: list[PropertyAtom],
    schema_path: str,
    workdir: Path,
) -> list[SymbolicCheck]:
    """Check 2: pairwise floor-implies-ceiling on the same action.

    Returns one SymbolicCheck per pairwise check actually run. If no
    same-action prior atoms of the opposite kind exist, returns an
    empty list (consistency is trivial).
    """
    out: list[SymbolicCheck] = []
    if atom.constraint_type == "liveness":
        return out
    if atom.constraint_type == "disjointness":
        # Disjointness atoms are sugar: during plan compilation they patch
        # same-action floors with ``!(disjoint_target_body)``. Checking the raw
        # disjointness ceiling against raw prior floors reports a false
        # inconsistency for exactly the cases the patch is meant to repair.
        # Stage 1.75 runs the patched plan-level consistency check.
        return out

    new_role = _ceiling_or_floor(atom)
    if new_role is None:
        return out

    for prior in prior_atoms:
        if prior.constraint_type == "disjointness":
            # Symmetric case: a later floor will be patched by the prior
            # disjointness during compile-down, so raw pairwise comparison is
            # intentionally deferred to Stage 1.75.
            continue
        if prior.action != atom.action:
            continue
        prior_role = _ceiling_or_floor(prior)
        if prior_role is None:
            continue
        if prior_role == new_role:
            # ceiling+ceiling and floor+floor are trivially consistent.
            continue

        floor_atom = atom if new_role == "floor" else prior
        ceiling_atom = prior if new_role == "floor" else atom

        floor_path = workdir / f"{floor_atom.name}_floor.cedar"
        ceiling_path = workdir / f"{ceiling_atom.name}_ceiling.cedar"
        floor_path.write_text(floor_atom.reference_cedar)
        ceiling_path.write_text(ceiling_atom.reference_cedar)
        principal_type, resource_type = _principal_resource(atom)

        passed, output = _run_symcc(
            schema_path,
            principal_type,
            atom.action,
            resource_type,
            "implies",
            ["--policies1", str(floor_path), "--policies2", str(ceiling_path)],
        )
        out.append(
            SymbolicCheck(
                name=f"joint-consistency-with-{prior.name}",
                passed=passed,
                detail="" if passed else (
                    f"floor {floor_atom.name} not contained in ceiling {ceiling_atom.name}"
                    "\nFloor reference:\n"
                    f"{floor_atom.reference_cedar.strip()}"
                    "\nCeiling reference:\n"
                    f"{ceiling_atom.reference_cedar.strip()}"
                    "\nCedar symcc output:\n"
                    f"{output.strip()[:1000]}"
                ),
            ),
        )

    out.extend(_check_same_role_duplicates(atom, prior_atoms, schema_path, workdir))
    return out


def _check_same_role_duplicates(
    atom: PropertyAtom,
    prior_atoms: list[PropertyAtom],
    schema_path: str,
    workdir: Path,
) -> list[SymbolicCheck]:
    """Flag same-action same-role atoms with equivalent match conditions."""
    out: list[SymbolicCheck] = []
    role = _ceiling_or_floor(atom)
    if role is None or atom.constraint_type == "disjointness":
        return out

    atom_path = workdir / f"{atom.name}_dup.cedar"
    atom_path.write_text(atom.reference_cedar)
    principal_type, resource_type = _principal_resource(atom)
    for prior in prior_atoms:
        if prior.action != atom.action:
            continue
        if prior.constraint_type == "disjointness":
            continue
        if _ceiling_or_floor(prior) != role:
            continue
        prior_path = workdir / f"{prior.name}_dup_prior.cedar"
        prior_path.write_text(prior.reference_cedar)
        signal = _run_symcc_signal(
            schema_path,
            principal_type,
            atom.action,
            resource_type,
            "matches-equivalent",
            ["--policy1", str(atom_path), "--policy2", str(prior_path)],
            candidate_excerpt=atom.reference_cedar,
            reference_excerpt=prior.reference_cedar,
        )
        if signal.tool_error:
            out.append(
                SymbolicCheck(
                    name=f"duplicate-detection-with-{prior.name}",
                    passed=False,
                    detail=signal.raw_output,
                ),
            )
        elif signal.passed:
            out.append(
                SymbolicCheck(
                    name=f"duplicate-detection-with-{prior.name}",
                    passed=True,
                    detail="WARNING: match condition equivalent to prior same-action atom",
                ),
            )
    return out


def _ceiling_or_floor(atom: PropertyAtom) -> Optional[str]:
    """Return ``"ceiling"`` or ``"floor"`` for an atom; ``None`` for liveness.

    Sugar atoms (``rate_limit``, ``disjointness``) compile to ceilings.
    """
    if atom.constraint_type == "ceiling":
        return "ceiling"
    if atom.constraint_type == "floor":
        return "floor"
    if atom.constraint_type in ("rate_limit", "disjointness"):
        return "ceiling"
    return None


def _check_sugar_universal(
    atom: PropertyAtom,
    schema_path: str,
    workdir: Path,
) -> SymbolicCheck:
    """Check 4: sugar-specific universal claim.

    This is a structural check rather than a complete theorem for every
    sugar form. Primitive ceiling/floor/liveness atoms are fully checked
    through the normal symcc paths.
    """
    if atom.constraint_type == "disjointness":
        target = atom.disjoint_target_body or ""
        if target and (f"!({target})" not in atom.reference_cedar
                       and f"!{target}" not in atom.reference_cedar):
            return SymbolicCheck(
                name="sugar-universal",
                passed=False,
                detail=(
                    "disjointness encoding does not appear to negate "
                    f"target body {target!r}"
                ),
            )
        principal_type, resource_type = _principal_resource(atom)
        atom_path = workdir / f"{atom.name}_disjoint_reference.cedar"
        target_path = workdir / f"{atom.name}_disjoint_target.cedar"
        atom_path.write_text(atom.reference_cedar)
        target_path.write_text(
            f'permit (principal, action == {_action_literal(atom.action)}, resource)\n'
            f"when {{ {target} }};\n",
        )
        signal = _run_symcc_signal(
            schema_path,
            principal_type,
            atom.action,
            resource_type,
            "matches-disjoint",
            ["--policy1", str(atom_path), "--policy2", str(target_path)],
            candidate_excerpt=atom.reference_cedar,
            reference_excerpt=target_path.read_text(),
        )
        if signal.tool_error:
            return SymbolicCheck(
                name="sugar-universal",
                passed=False,
                detail=signal.raw_output,
            )
        if not signal.passed:
            return SymbolicCheck(
                name="sugar-universal",
                passed=False,
                detail="disjointness reference can still match target body\n" + signal.compact_detail(),
            )
        return SymbolicCheck(
            name="sugar-universal",
            passed=True,
            detail="matches-disjoint verified against target body",
        )
    if atom.constraint_type == "rate_limit":
        counter = atom.rate_limit_counter_attr or ""
        threshold = atom.rate_limit_threshold
        if counter and threshold is not None:
            if counter not in atom.reference_cedar or str(threshold) not in atom.reference_cedar:
                return SymbolicCheck(
                    name="sugar-universal",
                    passed=False,
                    detail=(
                        f"rate_limit encoding does not reference counter {counter!r} "
                        f"or threshold {threshold}"
                    ),
                )
        return SymbolicCheck(
            name="sugar-universal",
            passed=True,
            detail="syntactic rate_limit sanity check ok (full check deferred)",
        )
    # Primitives carry no sugar-specific universal claim.
    return SymbolicCheck(
        name="sugar-universal",
        passed=True,
        detail="not applicable to primitives",
    )


# ---------------------------------------------------------------------------
# Top-level: symbolic_verify_atom (§4.3).
# ---------------------------------------------------------------------------

def symbolic_verify_atom(
    atom: PropertyAtom,
    schema_path: str,
    prior_atoms: Optional[list[PropertyAtom]] = None,
    workdir: Optional[Path] = None,
) -> SymbolicVerificationResult:
    """Run the four symcc checks. Mutates atom in place.

    Sets ``atom.symbolic_verified`` to True iff every check passed.
    Populates ``atom.symbolic_verification_log`` with one line per check.
    """
    prior_atoms = prior_atoms or []
    workdir = workdir or Path(tempfile.mkdtemp(prefix="autocedar_grounding_"))
    workdir.mkdir(parents=True, exist_ok=True)

    result = SymbolicVerificationResult(atom_name=atom.name)

    # Check 3: type correctness.
    if atom.constraint_type == "liveness" and not atom.reference_cedar:
        # Liveness has no reference body to validate.
        result.checks.append(SymbolicCheck(name="type-correct", passed=True, detail="n/a"))
    else:
        result.checks.append(_check_type_correctness(atom, schema_path, workdir))

    # Check 5: schema-aware identity consistency. Cedar validation can pass
    # even when a policy compares User::"alice" to Patient::"alice".
    result.checks.append(_check_identity_consistency(atom, schema_path))

    # Check 1: satisfiability.
    result.checks.append(_check_satisfiability(atom, schema_path, workdir))

    # Extra SymCC arsenal: runtime safety, individual-policy vacuity, and
    # broadness diagnostics. These are generic verifier signals, not domain
    # repair rules.
    result.checks.append(_check_never_errors(atom, schema_path, workdir))
    result.checks.extend(_check_match_shape(atom, schema_path, workdir))

    # Check 2: joint consistency.
    result.checks.extend(_check_joint_consistency(atom, prior_atoms, schema_path, workdir))

    # Check 4: sugar-specific universal claim.
    result.checks.append(_check_sugar_universal(atom, schema_path, workdir))

    # Mutate atom.
    atom.symbolic_verified = result.all_passed
    atom.symbolic_verification_log = result.log_lines()
    return result


# ---------------------------------------------------------------------------
# Adversarial-example pipeline (§4.4–§4.5).
# ---------------------------------------------------------------------------

# Type alias for the LLM call that proposes alternatives. Stubbable.
AlternativeProposer = Callable[[PropertyAtom, str, int], list[AlternativeEncoding]]


def _stub_alternative_proposer(
    atom: PropertyAtom,
    schema_text: str,
    n: int,
) -> list[AlternativeEncoding]:
    """Offline alternative proposer: returns an empty list by default.

    Production callers may inject an LLM-backed proposer. Tests can pass
    alternatives directly via ``generate_adversarial_examples(...,
    alternatives=...)``.
    """
    return []


def find_distinguishing_request(
    chosen_cedar: str,
    alternative: AlternativeEncoding,
    schema_path: str,
    principal_type: str,
    action: str,
    resource_type: str,
    workdir: Optional[Path] = None,
) -> Optional[Example]:
    """Use symcc to find a request where chosen and alternative disagree.

    Runs ``cedar symcc implies`` in both directions. If either direction
    fails, the counterexample is a distinguishing request and we return
    an Example labeled with which way the disagreement runs. If both
    directions pass, the encodings are equivalent on this action's
    request space and we return ``None``.
    """
    workdir = workdir or Path(tempfile.mkdtemp(prefix="autocedar_distinguish_"))
    workdir.mkdir(parents=True, exist_ok=True)

    chosen_path = workdir / "chosen.cedar"
    alt_path = workdir / f"alt_{alternative.label}.cedar"
    chosen_path.write_text(chosen_cedar)
    alt_path.write_text(alternative.cedar_text)

    # Direction 1: chosen match condition ⊆ alt match condition? If not,
    # there's a request where chosen permits and alt denies.
    chosen_implies_alt, out_a = _run_symcc(
        schema_path,
        principal_type,
        action,
        resource_type,
        "matches-implies",
        ["--policy1", str(chosen_path), "--policy2", str(alt_path)],
    )
    if not chosen_implies_alt:
        if _is_symcc_tool_error(out_a):
            return None
        return Example(
            description=(
                f"chosen permits, alternative '{alternative.label}' denies "
                f"(symcc counterexample): "
                f"{_summarize_counterexample(out_a)}"
            ),
            request_dict={"counterexample_text": _summarize_counterexample(out_a)},
            decision_under_chosen="permit",
            decisions_under_alternatives={alternative.label: "deny"},
            diagnostic_for=[alternative.label],
        )

    # Direction 2: alt match condition ⊆ chosen match condition? If not,
    # there's a request where alt permits and chosen denies.
    alt_implies_chosen, out_b = _run_symcc(
        schema_path,
        principal_type,
        action,
        resource_type,
        "matches-implies",
        ["--policy1", str(alt_path), "--policy2", str(chosen_path)],
    )
    if not alt_implies_chosen:
        if _is_symcc_tool_error(out_b):
            return None
        return Example(
            description=(
                f"alternative '{alternative.label}' permits, chosen denies "
                f"(symcc counterexample): "
                f"{_summarize_counterexample(out_b)}"
            ),
            request_dict={"counterexample_text": _summarize_counterexample(out_b)},
            decision_under_chosen="deny",
            decisions_under_alternatives={alternative.label: "permit"},
            diagnostic_for=[alternative.label],
        )

    # Both directions pass — encodings are equivalent.
    return None


def _summarize_counterexample(symcc_output: str) -> str:
    """Extract a one-line summary from symcc's stdout for UI display."""
    for line in symcc_output.splitlines():
        line = line.strip()
        if line.startswith("Counterexample") or line.startswith("counterexample"):
            return line
    # Fall back to first non-empty line under 200 chars.
    for line in symcc_output.splitlines():
        line = line.strip()
        if line and "VERIFIED" not in line and len(line) < 200:
            return line
    return symcc_output[:200]


def generate_adversarial_examples(
    atom: PropertyAtom,
    schema_path: str,
    schema_text: str = "",
    alternatives: Optional[list[AlternativeEncoding]] = None,
    propose: AlternativeProposer = _stub_alternative_proposer,
    n_alternatives: int = 3,
    workdir: Optional[Path] = None,
) -> list[Example]:
    """Compose: propose alternatives → find distinguishers → format examples.

    Mutates ``atom.examples_adversarial`` and ``atom.alternatives_considered``.

    Callers can pass a list of pre-built ``alternatives`` directly to skip
    proposal, or wire ``propose`` to an LLM-backed alternative proposer.
    """
    if atom.constraint_type == "liveness":
        return []

    if alternatives is None:
        alternatives = propose(atom, schema_text, n_alternatives)

    workdir = workdir or Path(tempfile.mkdtemp(prefix="autocedar_adv_"))
    workdir.mkdir(parents=True, exist_ok=True)

    principal_type, resource_type = _principal_resource(atom)

    out: list[Example] = []
    surviving_alts: list[AlternativeEncoding] = []
    for alt in alternatives:
        ex = find_distinguishing_request(
            chosen_cedar=atom.reference_cedar,
            alternative=alt,
            schema_path=schema_path,
            principal_type=principal_type,
            action=atom.action,
            resource_type=resource_type,
            workdir=workdir,
        )
        if ex is None:
            continue  # Equivalent alternative — no diagnostic value.
        out.append(ex)
        surviving_alts.append(alt)

    atom.examples_adversarial = out
    atom.alternatives_considered = surviving_alts
    return out
