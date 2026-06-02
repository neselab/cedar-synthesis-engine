"""Integration tests for ``autocedar.grounding``.

These tests invoke the real Cedar CLI (``cedar symcc`` + ``cedar
validate``) and CVC5. They are skipped when the binaries are not on
disk at the locations grounding.py expects.

See ``docs/HITL_STEP_B_PLAN.md`` §9 acceptance criteria 2 and 3.
"""

from __future__ import annotations

import os
import textwrap
from pathlib import Path

import pytest

from autocedar.atoms import (
    AlternativeEncoding,
    PropertyAtom,
)
from autocedar.grounding import (
    CEDAR_PATH,
    CVC5_PATH,
    find_distinguishing_request,
    generate_adversarial_examples,
    symbolic_verify_atom,
)

_HAVE_CEDAR = os.path.isfile(CEDAR_PATH) and os.access(CEDAR_PATH, os.X_OK)
_HAVE_CVC5 = os.path.isfile(CVC5_PATH) and os.access(CVC5_PATH, os.X_OK)
_HAVE_SOLVERS = _HAVE_CEDAR and _HAVE_CVC5

requires_solvers = pytest.mark.skipif(
    not _HAVE_SOLVERS,
    reason=f"Cedar/CVC5 not available (CEDAR={CEDAR_PATH}, CVC5={CVC5_PATH})",
)


# ---------------------------------------------------------------------------
# Test fixtures: minimal schema + atoms.
# ---------------------------------------------------------------------------

MINIMAL_SCHEMA = textwrap.dedent("""\
    entity User {
        role: String,
        isAdmin: Bool,
    };

    entity Resource {
        owner: User,
        isPublic: Bool,
    };

    action read appliesTo {
        principal: [User],
        resource: [Resource],
    };

    action write appliesTo {
        principal: [User],
        resource: [Resource],
    };
""")


@pytest.fixture
def schema_path(tmp_path: Path) -> str:
    schema_file = tmp_path / "schema.cedarschema"
    schema_file.write_text(MINIMAL_SCHEMA)
    return str(schema_file)


@pytest.fixture
def workdir(tmp_path: Path) -> Path:
    wd = tmp_path / "work"
    wd.mkdir()
    return wd


def _owner_only_ceiling() -> PropertyAtom:
    return PropertyAtom(
        name="owner_only_read_ceiling",
        rationale="bound on read",
        plain_english_summary="Only the resource owner may read",
        source_excerpt="Only the owner can read.",
        constraint_type="ceiling",
        action="read",
        principal_types=["User"],
        resource_types=["Resource"],
        reference_cedar=(
            'permit (principal is User, action == Action::"read", resource is Resource)\n'
            "when { principal == resource.owner };\n"
        ),
    )


def _owner_must_read_floor() -> PropertyAtom:
    return PropertyAtom(
        name="owner_must_read_floor",
        rationale="owner must be permitted to read",
        plain_english_summary="The owner MUST be permitted to read",
        source_excerpt="The owner can always read.",
        constraint_type="floor",
        action="read",
        principal_types=["User"],
        resource_types=["Resource"],
        reference_cedar=(
            'permit (principal is User, action == Action::"read", resource is Resource)\n'
            "when { principal == resource.owner };\n"
        ),
    )


def _admin_must_read_floor() -> PropertyAtom:
    """A floor that's INCONSISTENT with the owner-only ceiling on read."""
    return PropertyAtom(
        name="admin_must_read_floor",
        rationale="admin must read",
        plain_english_summary="Admins MUST be permitted to read",
        source_excerpt="Admins can read.",
        constraint_type="floor",
        action="read",
        principal_types=["User"],
        resource_types=["Resource"],
        reference_cedar=(
            'permit (principal is User, action == Action::"read", resource is Resource)\n'
            "when { principal.isAdmin };\n"
        ),
    )


def _vacuous_ceiling() -> PropertyAtom:
    """A ceiling whose body is `false` — should fail the satisfiability check."""
    return PropertyAtom(
        name="vacuous",
        rationale="dead-rule encoding",
        plain_english_summary="vacuous",
        source_excerpt="...",
        constraint_type="ceiling",
        action="read",
        principal_types=["User"],
        resource_types=["Resource"],
        reference_cedar=(
            'permit (principal is User, action == Action::"read", resource is Resource)\n'
            "when { false };\n"
        ),
    )


def _liveness_atom() -> PropertyAtom:
    return PropertyAtom(
        name="liveness_read",
        rationale="liveness",
        plain_english_summary="At least one read must be permitted",
        source_excerpt="(implicit)",
        constraint_type="liveness",
        action="read",
        principal_types=["User"],
        resource_types=["Resource"],
    )


# ---------------------------------------------------------------------------
# Symbolic verification (§4.1–§4.3).
# ---------------------------------------------------------------------------

@requires_solvers
def test_known_good_atom_passes_all_four_checks(
    schema_path: str, workdir: Path,
) -> None:
    atom = _owner_only_ceiling()
    result = symbolic_verify_atom(atom, schema_path, prior_atoms=[], workdir=workdir)
    assert result.all_passed, f"checks failed: {result.log_lines()}"
    assert atom.symbolic_verified is True
    # Log entries cover the four-check shape.
    log = atom.symbolic_verification_log
    assert any("type-correct" in line for line in log)
    assert any("satisfiable" in line for line in log)
    assert any("sugar-universal" in line for line in log)


@requires_solvers
def test_vacuous_atom_fails_satisfiability(
    schema_path: str, workdir: Path,
) -> None:
    atom = _vacuous_ceiling()
    result = symbolic_verify_atom(atom, schema_path, prior_atoms=[], workdir=workdir)
    assert not result.all_passed
    assert atom.symbolic_verified is False
    sat_check = next(c for c in result.checks if c.name == "satisfiable")
    assert sat_check.passed is False
    assert "vacuous" in sat_check.detail.lower()


@requires_solvers
def test_floor_inconsistent_with_ceiling_caught_in_joint_consistency(
    schema_path: str, workdir: Path,
) -> None:
    """An admin-must-read floor is unsat against an owner-only ceiling."""
    ceiling = _owner_only_ceiling()
    # Verify the ceiling alone passes (so prior context is solid).
    symbolic_verify_atom(ceiling, schema_path, prior_atoms=[], workdir=workdir)
    assert ceiling.symbolic_verified

    # Now add an inconsistent floor. Joint consistency check should fail.
    floor = _admin_must_read_floor()
    result = symbolic_verify_atom(
        floor, schema_path, prior_atoms=[ceiling], workdir=workdir,
    )
    jc_checks = [c for c in result.checks if c.name.startswith("joint-consistency")]
    assert any(not c.passed for c in jc_checks), (
        f"expected at least one joint-consistency check to fail; got {result.log_lines()}"
    )
    assert floor.symbolic_verified is False


@requires_solvers
def test_consistent_floor_passes_joint_consistency(
    schema_path: str, workdir: Path,
) -> None:
    """A floor that's consistent with the ceiling passes."""
    ceiling = _owner_only_ceiling()
    symbolic_verify_atom(ceiling, schema_path, prior_atoms=[], workdir=workdir)

    floor = _owner_must_read_floor()
    result = symbolic_verify_atom(
        floor, schema_path, prior_atoms=[ceiling], workdir=workdir,
    )
    assert result.all_passed, f"checks failed: {result.log_lines()}"
    assert floor.symbolic_verified is True


@requires_solvers
def test_liveness_atom_skips_reference_checks(
    schema_path: str, workdir: Path,
) -> None:
    atom = _liveness_atom()
    result = symbolic_verify_atom(atom, schema_path, prior_atoms=[], workdir=workdir)
    assert atom.symbolic_verified is True
    # Type-correct + satisfiable + sugar-universal entries present.
    names = [c.name for c in result.checks]
    assert "type-correct" in names
    assert "satisfiable" in names


@requires_solvers
def test_sugar_disjointness_universal_check_runs(
    schema_path: str, workdir: Path,
) -> None:
    """Disjointness atom whose encoding negates target_body passes the
    sugar-universal sanity check."""
    target = "resource.isPublic"
    atom = PropertyAtom(
        name="public_resources_off_limits_disj",
        rationale="public resources are off-limits to writes via this atom",
        plain_english_summary="public resources may not be written via this branch",
        source_excerpt="...",
        constraint_type="disjointness",
        action="write",
        principal_types=["User"],
        resource_types=["Resource"],
        reference_cedar=(
            'permit (principal is User, action == Action::"write", resource is Resource)\n'
            "when { !(resource.isPublic) };\n"
        ),
        disjoint_with="public_resources",
        disjoint_target_body=target,
    )
    result = symbolic_verify_atom(atom, schema_path, prior_atoms=[], workdir=workdir)
    sugar = next(c for c in result.checks if c.name == "sugar-universal")
    assert sugar.passed, sugar.detail


@requires_solvers
def test_sugar_disjointness_universal_check_flags_missing_negation(
    schema_path: str, workdir: Path,
) -> None:
    """A disjointness atom whose encoding does NOT contain the negated
    target body fails the sugar-universal sanity check."""
    atom = PropertyAtom(
        name="bad_disj",
        rationale="missing negation",
        plain_english_summary="...",
        source_excerpt="...",
        constraint_type="disjointness",
        action="write",
        principal_types=["User"],
        resource_types=["Resource"],
        reference_cedar=(
            # Note: deliberately does NOT contain !(resource.isPublic).
            'permit (principal is User, action == Action::"write", resource is Resource)\n'
            "when { principal.isAdmin };\n"
        ),
        disjoint_with="public_resources",
        disjoint_target_body="resource.isPublic",
    )
    result = symbolic_verify_atom(atom, schema_path, prior_atoms=[], workdir=workdir)
    sugar = next(c for c in result.checks if c.name == "sugar-universal")
    assert not sugar.passed
    assert "negate" in sugar.detail.lower() or "does not appear" in sugar.detail.lower()


# ---------------------------------------------------------------------------
# Adversarial examples (§4.4–§4.5).
# ---------------------------------------------------------------------------

@requires_solvers
def test_find_distinguishing_request_returns_example_when_alternatives_diverge(
    schema_path: str, workdir: Path,
) -> None:
    """chosen = owner-only; alt = owner-or-admin. They diverge on
    (principal != owner, principal.isAdmin = true)."""
    chosen = (
        'permit (principal is User, action == Action::"read", resource is Resource)\n'
        "when { principal == resource.owner };\n"
    )
    alt = AlternativeEncoding(
        label="owner-or-admin",
        interpretive_choice="admins also permitted",
        cedar_text=(
            'permit (principal is User, action == Action::"read", resource is Resource)\n'
            "when { principal == resource.owner || principal.isAdmin };\n"
        ),
    )
    example = find_distinguishing_request(
        chosen_cedar=chosen,
        alternative=alt,
        schema_path=schema_path,
        principal_type="User",
        action="read",
        resource_type="Resource",
        workdir=workdir,
    )
    assert example is not None
    # Exactly one direction's decisions are recorded.
    assert "owner-or-admin" in example.decisions_under_alternatives
    # The two decisions disagree (the whole point of a distinguisher).
    chosen_dec = example.decision_under_chosen
    alt_dec = example.decisions_under_alternatives["owner-or-admin"]
    assert chosen_dec != alt_dec


@requires_solvers
def test_find_distinguishing_request_returns_none_for_equivalent_encodings(
    schema_path: str, workdir: Path,
) -> None:
    """Two syntactically-different but semantically-equivalent encodings
    should produce no distinguisher."""
    chosen = (
        'permit (principal is User, action == Action::"read", resource is Resource)\n'
        "when { principal == resource.owner };\n"
    )
    # `principal == resource.owner` is equivalent to `resource.owner == principal`.
    alt = AlternativeEncoding(
        label="reversed-equality",
        interpretive_choice="reversed operands",
        cedar_text=(
            'permit (principal is User, action == Action::"read", resource is Resource)\n'
            "when { resource.owner == principal };\n"
        ),
    )
    example = find_distinguishing_request(
        chosen_cedar=chosen,
        alternative=alt,
        schema_path=schema_path,
        principal_type="User",
        action="read",
        resource_type="Resource",
        workdir=workdir,
    )
    assert example is None


@requires_solvers
def test_generate_adversarial_examples_with_explicit_alternatives(
    schema_path: str, workdir: Path,
) -> None:
    """The end-to-end generator drops equivalent alternatives and keeps
    distinguishers in atom.examples_adversarial."""
    atom = _owner_only_ceiling()
    alts = [
        AlternativeEncoding(
            label="owner-or-admin",
            interpretive_choice="admins also permitted",
            cedar_text=(
                'permit (principal is User, action == Action::"read", resource is Resource)\n'
                "when { principal == resource.owner || principal.isAdmin };\n"
            ),
        ),
        AlternativeEncoding(
            label="reversed-equality",
            interpretive_choice="reversed operands (equivalent)",
            cedar_text=(
                'permit (principal is User, action == Action::"read", resource is Resource)\n'
                "when { resource.owner == principal };\n"
            ),
        ),
    ]
    examples = generate_adversarial_examples(
        atom=atom,
        schema_path=schema_path,
        alternatives=alts,
        workdir=workdir,
    )
    # The reversed-equality alternative should drop out (equivalent → no
    # diagnostic value); only owner-or-admin survives.
    labels = {a.label for a in atom.alternatives_considered}
    assert labels == {"owner-or-admin"}
    assert len(examples) == 1
