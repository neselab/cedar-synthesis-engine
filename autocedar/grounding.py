"""Symbolic verification + adversarial-example generation for Stage 2 atoms.

The symbolic checks per atom are:

1. Satisfiability — there exists a request the encoding permits/denies.
2. Joint consistency — atom is jointly satisfiable with previously-
   approved atoms (pairwise floor-implies-ceiling on same action).
3. Type correctness — ``cedar validate`` against the composed schema.
4. Sugar-specific universal claims — structural sanity checks for
   sugar atoms such as disjointness and rate limits.

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
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from autocedar.atoms import (
    AlternativeEncoding,
    Example,
    PropertyAtom,
)

CEDAR_PATH = os.environ.get("CEDAR", os.path.expanduser("~/.cargo/bin/cedar"))
CVC5_PATH = os.environ.get("CVC5", os.path.expanduser("~/.local/bin/cvc5"))


# ---------------------------------------------------------------------------
# Result objects.
# ---------------------------------------------------------------------------

@dataclass
class SymbolicCheck:
    """Result of one of the four atom-level symcc checks (§4.1)."""

    name: str  # "satisfiable" | "joint-consistency-with-<atom>" | "type-correct" | "sugar-universal"
    passed: bool
    detail: str = ""


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
    cmd = [
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
    ] + extra_args
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
    except subprocess.TimeoutExpired:
        return False, "symcc timed out"
    except FileNotFoundError:
        return False, f"cedar binary not found at {CEDAR_PATH}"
    output = (result.stdout.strip() + "\n" + result.stderr.strip()).strip()
    return ("VERIFIED" in output), output


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


def _check_satisfiability(
    atom: PropertyAtom,
    schema_path: str,
    workdir: Path,
) -> SymbolicCheck:
    """Check 1: the encoding is not vacuous (i.e. not always-denies)."""
    if atom.constraint_type == "liveness":
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
    if always_denies:
        return SymbolicCheck(
            name="satisfiable",
            passed=False,
            detail="encoding is vacuous (always denies)",
        )
    return SymbolicCheck(name="satisfiable", passed=True)


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

    new_role = _ceiling_or_floor(atom)
    if new_role is None:
        return out

    for prior in prior_atoms:
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
        # Sanity check: reference encoding mentions the negated body.
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
        return SymbolicCheck(
            name="sugar-universal",
            passed=True,
            detail="syntactic disjointness sanity check ok",
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
    if atom.constraint_type == "liveness":
        # Liveness has no reference body to validate.
        result.checks.append(SymbolicCheck(name="type-correct", passed=True, detail="n/a"))
    else:
        result.checks.append(_check_type_correctness(atom, schema_path, workdir))

    # Check 1: satisfiability.
    result.checks.append(_check_satisfiability(atom, schema_path, workdir))

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

    # Direction 1: chosen ⊆ alt? If not, there's a request where chosen
    # permits and alt denies.
    chosen_implies_alt, out_a = _run_symcc(
        schema_path,
        principal_type,
        action,
        resource_type,
        "implies",
        ["--policies1", str(chosen_path), "--policies2", str(alt_path)],
    )
    if not chosen_implies_alt:
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

    # Direction 2: alt ⊆ chosen? If not, there's a request where alt
    # permits and chosen denies.
    alt_implies_chosen, out_b = _run_symcc(
        schema_path,
        principal_type,
        action,
        resource_type,
        "implies",
        ["--policies1", str(alt_path), "--policies2", str(chosen_path)],
    )
    if not alt_implies_chosen:
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
