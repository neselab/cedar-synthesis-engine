"""Tests for ``autocedar.plan_verification``.

Covers acceptance criteria 5 (Stage 1.75 unsat detection) and 6
(Stage 2.5 traceback) from ``docs/HITL_STEP_B_PLAN.md`` §9.
"""

from __future__ import annotations

import os
import textwrap
from pathlib import Path

import pytest

from autocedar.atoms import PropertyAtom, VerificationPlanDraft
from autocedar.grounding import CEDAR_PATH, CVC5_PATH
from autocedar.plan_verification import (
    generate_atom_traceback,
    symbolic_consistency_check,
)
from autocedar.plan_verification import (
    _extract_attribute_paths,
    _split_clauses,
)

_HAVE_SOLVERS = (
    os.path.isfile(CEDAR_PATH)
    and os.access(CEDAR_PATH, os.X_OK)
    and os.path.isfile(CVC5_PATH)
    and os.access(CVC5_PATH, os.X_OK)
)
requires_solvers = pytest.mark.skipif(
    not _HAVE_SOLVERS, reason="Cedar/CVC5 not available",
)


# ---------------------------------------------------------------------------
# Fixtures.
# ---------------------------------------------------------------------------

MINIMAL_SCHEMA = textwrap.dedent("""\
    entity User {
        role: String,
        isAdmin: Bool,
    };

    entity Resource {
        owner: User,
        legalHold: Bool,
    };

    action read appliesTo {
        principal: [User],
        resource: [Resource],
    };
""")


@pytest.fixture
def schema_path(tmp_path: Path) -> str:
    p = tmp_path / "schema.cedarschema"
    p.write_text(MINIMAL_SCHEMA)
    return str(p)


def _floor(name: str, when: str) -> PropertyAtom:
    return PropertyAtom(
        name=name,
        rationale="floor",
        plain_english_summary=name,
        source_excerpt="...",
        constraint_type="floor",
        action="read",
        principal_types=["User"],
        resource_types=["Resource"],
        reference_cedar=(
            'permit (principal is User, action == Action::"read", resource is Resource)\n'
            f"when {{ {when} }};\n"
        ),
    )


def _ceiling(name: str, when: str) -> PropertyAtom:
    return PropertyAtom(
        name=name,
        rationale="ceiling",
        plain_english_summary=name,
        source_excerpt="...",
        constraint_type="ceiling",
        action="read",
        principal_types=["User"],
        resource_types=["Resource"],
        reference_cedar=(
            'permit (principal is User, action == Action::"read", resource is Resource)\n'
            f"when {{ {when} }};\n"
        ),
    )


# ---------------------------------------------------------------------------
# Stage 1.75 — symbolic_consistency_check.
# ---------------------------------------------------------------------------

@requires_solvers
def test_consistent_plan_returns_unsat_false(schema_path: str) -> None:
    plan = VerificationPlanDraft(
        properties=[
            _ceiling("owner_only", "principal == resource.owner"),
            _floor("owner_must", "principal == resource.owner"),
        ],
    )
    result = symbolic_consistency_check(plan, schema_path)
    assert result.unsat is False
    assert result.core == []


@requires_solvers
def test_inconsistent_plan_returns_unsat_with_core(schema_path: str) -> None:
    """Owner-only ceiling + admin-must-read floor is jointly unsat:
    an admin who is not the owner is required to be permitted by the
    floor but forbidden by the ceiling."""
    plan = VerificationPlanDraft(
        properties=[
            _ceiling("owner_only", "principal == resource.owner"),
            _floor("admin_must", "principal.isAdmin"),
        ],
    )
    result = symbolic_consistency_check(plan, schema_path)
    assert result.unsat is True
    # Both atoms participate in the unsat core.
    assert "owner_only" in result.core
    assert "admin_must" in result.core
    assert "not contained" in result.detail


@requires_solvers
def test_consistency_check_ignores_different_actions(schema_path: str) -> None:
    """A floor on ``read`` and a ceiling on ``read`` that contradict
    are caught — but the same pair on different actions is not (we
    do not cross-check actions)."""
    # Different-action atoms: floor on read, ceiling on a hypothetical
    # `write` action. Should NOT trigger unsat across actions.
    write_ceiling = PropertyAtom(
        name="write_owner_only",
        rationale="...",
        plain_english_summary="...",
        source_excerpt="...",
        constraint_type="ceiling",
        action="write",  # different action
        principal_types=["User"],
        resource_types=["Resource"],
        reference_cedar=(
            'permit (principal is User, action == Action::"write", resource is Resource)\n'
            "when { principal == resource.owner };\n"
        ),
    )
    read_floor = _floor("admin_must_read", "principal.isAdmin")
    plan = VerificationPlanDraft(properties=[write_ceiling, read_floor])
    # The same-action pair has no ceiling on read → no check runs;
    # the cross-action ceiling is irrelevant.
    result = symbolic_consistency_check(plan, schema_path)
    assert result.unsat is False


# ---------------------------------------------------------------------------
# Helper-level tests for clause splitting and attribute extraction.
# ---------------------------------------------------------------------------

def test_split_clauses_handles_multiple_permits() -> None:
    text = textwrap.dedent("""\
        permit (principal, action, resource)
        when { principal.role == "admin" };

        permit (principal, action, resource)
        when { resource.isPublic };
    """)
    clauses = _split_clauses(text)
    assert len(clauses) == 2
    assert all("permit" in c for c in clauses)


def test_split_clauses_respects_nested_braces() -> None:
    """A `when` body with nested record literals must not split early."""
    text = textwrap.dedent("""\
        permit (principal, action, resource)
        when {
            context.target == { id: "x", role: "admin" }
        };
    """)
    clauses = _split_clauses(text)
    assert len(clauses) == 1


def test_extract_attribute_paths() -> None:
    text = "principal.role == \"admin\" && resource.legalHold && context.now"
    paths = _extract_attribute_paths(text)
    assert "principal.role" in paths
    assert "resource.legalHold" in paths
    assert "context.now" in paths


# ---------------------------------------------------------------------------
# Stage 2.5 — generate_atom_traceback.
# ---------------------------------------------------------------------------

def _exact_match_atom() -> PropertyAtom:
    return PropertyAtom(
        name="owner_only_ceiling",
        rationale="...",
        plain_english_summary="The owner can read.",
        source_excerpt="The owner can read records. Reference uses principal.",
        constraint_type="ceiling",
        action="read",
        principal_types=["User"],
        resource_types=["Resource"],
        reference_cedar=(
            'permit (principal is User, action == Action::"read", resource is Resource)\n'
            "when { principal == resource.owner };\n"
        ),
    )


def test_traceback_populates_clauses_for_matching_action(tmp_path: Path) -> None:
    candidate_path = tmp_path / "candidate.cedar"
    candidate_path.write_text(
        'permit (principal is User, action == Action::"read", resource is Resource)\n'
        "when { principal == resource.owner };\n",
    )
    atom = _exact_match_atom()
    plan = VerificationPlanDraft(properties=[atom])

    traceback = generate_atom_traceback(plan, str(candidate_path))
    assert len(traceback) == 1
    entry = traceback[0]
    assert len(entry.clauses) == 1
    # Atom mutation: traceback_clauses is populated.
    assert atom.traceback_clauses == entry.clauses
    assert atom.traceback_flags == entry.flags


def test_traceback_no_flags_on_exact_match(tmp_path: Path) -> None:
    candidate_path = tmp_path / "candidate.cedar"
    candidate_path.write_text(
        'permit (principal is User, action == Action::"read", resource is Resource)\n'
        "when { principal == resource.owner };\n",
    )
    atom = _exact_match_atom()
    plan = VerificationPlanDraft(properties=[atom])

    generate_atom_traceback(plan, str(candidate_path))
    # No silent-divergence flags expected.
    assert atom.traceback_flags == []


def test_traceback_flags_attribute_not_in_atom_prose(tmp_path: Path) -> None:
    """Candidate uses ``principal.isAdmin`` — an attribute the atom never
    mentions. §6.3 flag should fire."""
    candidate_path = tmp_path / "candidate.cedar"
    candidate_path.write_text(
        'permit (principal is User, action == Action::"read", resource is Resource)\n'
        "when { principal.isAdmin };\n",
    )
    atom = _exact_match_atom()
    plan = VerificationPlanDraft(properties=[atom])

    generate_atom_traceback(plan, str(candidate_path))
    assert any(
        "uses-attribute-not-in-atom-prose" in f and "principal.isAdmin" in f
        for f in atom.traceback_flags
    )


def test_traceback_flags_multi_clause_interaction(tmp_path: Path) -> None:
    """Two clauses on the same action → multi-clause-interaction flag."""
    candidate_path = tmp_path / "candidate.cedar"
    candidate_path.write_text(
        'permit (principal is User, action == Action::"read", resource is Resource)\n'
        "when { principal == resource.owner };\n"
        "\n"
        'forbid (principal is User, action == Action::"read", resource is Resource)\n'
        "when { resource.legalHold };\n",
    )
    atom = _exact_match_atom()
    plan = VerificationPlanDraft(properties=[atom])

    generate_atom_traceback(plan, str(candidate_path))
    assert "multi-clause-interaction" in atom.traceback_flags


def test_traceback_flags_idiom_not_in_atom_encoding(tmp_path: Path) -> None:
    """Candidate uses ``unless`` — an idiom the atom's encoding doesn't
    use (atom uses only ``permit when``). §6.3 flag should fire."""
    candidate_path = tmp_path / "candidate.cedar"
    candidate_path.write_text(
        'permit (principal is User, action == Action::"read", resource is Resource)\n'
        "when { principal == resource.owner }\n"
        "unless { resource.legalHold };\n",
    )
    atom = _exact_match_atom()
    plan = VerificationPlanDraft(properties=[atom])

    generate_atom_traceback(plan, str(candidate_path))
    assert any(
        "idiom-not-in-atom-encoding" in f and "unless" in f
        for f in atom.traceback_flags
    )


def test_traceback_action_scope_isolation(tmp_path: Path) -> None:
    """Candidate clauses on a different action are NOT included in the
    traceback for an atom on ``read``."""
    candidate_path = tmp_path / "candidate.cedar"
    candidate_path.write_text(
        'permit (principal is User, action == Action::"read", resource is Resource)\n'
        "when { principal == resource.owner };\n"
        'permit (principal is User, action == Action::"write", resource is Resource)\n'
        "when { principal.isAdmin };\n",
    )
    atom = _exact_match_atom()  # action == "read"
    plan = VerificationPlanDraft(properties=[atom])

    generate_atom_traceback(plan, str(candidate_path))
    # Only the read-action clause should appear.
    assert len(atom.traceback_clauses) == 1
    assert "Action::\"read\"" in atom.traceback_clauses[0]
