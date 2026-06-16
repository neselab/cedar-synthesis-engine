"""End-to-end tests for ``autocedar.pipeline.author``.

Covers acceptance criteria 8 (pipeline skeleton) and 9 (corpus
logging) of ``docs/HITL_STEP_B_PLAN.md`` §9.

Stubbed LLM/proposer/synthesizer callbacks so these tests run without
a live LLM API key.
"""

from __future__ import annotations

import json
import os
import textwrap
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from autocedar.atoms import PropertyAtom
from autocedar.corpus import AtomDecision
from autocedar.grounding import CEDAR_PATH, CVC5_PATH
from autocedar.pipeline import author

_HAVE_SOLVERS = (
    os.path.isfile(CEDAR_PATH)
    and os.access(CEDAR_PATH, os.X_OK)
    and os.path.isfile(CVC5_PATH)
    and os.access(CVC5_PATH, os.X_OK)
)
requires_solvers = pytest.mark.skipif(
    not _HAVE_SOLVERS, reason="Cedar/CVC5 not available",
)


MINIMAL_SCHEMA = textwrap.dedent("""\
    entity User {
        role: String,
        isAdmin: Bool,
    };

    entity Resource {
        owner: User,
    };

    action read appliesTo {
        principal: [User],
        resource: [Resource],
    };
""")


@pytest.fixture
def workspace(tmp_path: Path) -> tuple[Path, Path]:
    spec_path = tmp_path / "policy_spec.md"
    spec_path.write_text("Owners can read their own resources.")
    schema_path = tmp_path / "schema.cedarschema"
    schema_path.write_text(MINIMAL_SCHEMA)
    return spec_path, schema_path


def _owner_only_ceiling() -> PropertyAtom:
    return PropertyAtom(
        name="owner_only_read",
        rationale="bound on read",
        plain_english_summary="Only the owner reads",
        source_excerpt="Owners can read their own resources.",
        constraint_type="ceiling",
        action="read",
        principal_types=["User"],
        resource_types=["Resource"],
        reference_cedar=(
            'permit (principal is User, action == Action::"read", resource is Resource)\n'
            "when { principal == resource.owner };\n"
        ),
    )


def _owner_must_floor() -> PropertyAtom:
    return PropertyAtom(
        name="owner_must_read",
        rationale="owner must be permitted",
        plain_english_summary="Owner must be permitted to read",
        source_excerpt="Owners can read their own resources.",
        constraint_type="floor",
        action="read",
        principal_types=["User"],
        resource_types=["Resource"],
        reference_cedar=(
            'permit (principal is User, action == Action::"read", resource is Resource)\n'
            "when { principal == resource.owner };\n"
        ),
    )


def _approve(atom: object) -> AtomDecision:
    return AtomDecision(
        atom_name=getattr(atom, "name", "?"),
        action="approve",
        intent_acknowledged_by_user=True,
        symbolic_verified=getattr(atom, "symbolic_verified", False),
    )


def _synthesize_stub(scenario_dir: Path) -> Path:
    candidate = scenario_dir / "candidate.cedar"
    candidate.write_text(
        "// test synthesizer output\n"
        "permit (principal, action, resource);\n",
    )
    return candidate


class _RecordingReviewer:
    def __init__(self) -> None:
        self.events: list[tuple[str, object]] = []

    def begin_stage(self, label: str, total: int) -> None:
        self.events.append(("begin", (label, total)))

    def end_stage(self, label: str, approved: int, rejected: int) -> None:
        self.events.append(("end", (label, approved, rejected)))

    def schema_ready(self, schema_text: str) -> None:
        self.events.append(("schema", schema_text))

    def property_plan_ready(self, properties: list[PropertyAtom]) -> None:
        self.events.append(("properties", len(properties)))

    def __call__(self, atom: object) -> AtomDecision:
        return _approve(atom)


# ---------------------------------------------------------------------------
# Acceptance criterion 8 — pipeline compiles + stubbed end-to-end run.
# ---------------------------------------------------------------------------

@requires_solvers
def test_author_runs_end_to_end_with_stubs(
    tmp_path: Path, workspace: tuple[Path, Path],
) -> None:
    """Full pipeline: stubbed proposers + auto-approve reviewer +
    stubbed synthesizer. Asserts no errors and the corpus directory
    layout per §9.1 exists at the end."""
    spec_path, schema_path = workspace
    output_dir = tmp_path / "out"

    def propose_property_atoms(spec_text: str, schema_path_arg: str) -> list[PropertyAtom]:
        return [_owner_only_ceiling(), _owner_must_floor()]

    result = author(
        spec_path=spec_path,
        output_dir=output_dir,
        session_id="t1",
        propose_property_atoms=propose_property_atoms,
        review_atom=_approve,
        synthesize=_synthesize_stub,
        schema_path_override=str(schema_path),
    )

    assert result.session_id == "t1"
    assert result.candidate_path.exists()
    assert result.final_user_approved is True

    session_dir = output_dir / "t1"

    # ── §9.1 directory layout assertions ────────────────────────────
    expected = [
        "input/policy_spec.md",
        "stage1/final_schema.cedarschema",
        "stage1/proposed_atoms.json",
        "stage1/decisions.json",
        "stage1/attribution_decisions.json",
        "stage1_5/amendments.json",
        "stage1_75/unsat_core.json",
        "stage2/proposed_atoms.json",
        "stage2/decisions.json",
        "stage2/attribution_decisions.json",
        "stage2/symbolic_verification_logs.json",
        "stage2/adversarial_examples.json",
        "stage2/final_plan/verification_plan.py",
        "stage2_5/traceback.json",
        "stage2_5/final_user_decision.json",
        "stage3/iterations/iter_1/candidate.cedar",
        "stage3/iterations/iter_1/verifier_feedback.json",
        "stage3/iterations/iter_1/critic_score.json",
        "stage3/final_candidate.cedar",
        "transcript.json",
    ]
    for rel in expected:
        assert (session_dir / rel).exists(), f"missing artifact {rel}"


def test_author_emits_review_stage_and_overview_hooks(
    tmp_path: Path, workspace: tuple[Path, Path],
) -> None:
    spec_path, schema_path = workspace
    reviewer = _RecordingReviewer()

    author(
        spec_path=spec_path,
        output_dir=tmp_path / "out",
        session_id="hooks",
        propose_property_atoms=lambda spec_text, schema_path_arg: [],
        review_atom=reviewer,
        synthesize=_synthesize_stub,
        schema_path_override=str(schema_path),
    )

    assert ("schema", MINIMAL_SCHEMA) in reviewer.events
    assert ("begin", ("Property intent review", 0)) in reviewer.events
    assert ("end", ("Property intent review", 0, 0)) in reviewer.events
    assert ("properties", 0) in reviewer.events


def test_author_rechecks_edited_property_atom(
    tmp_path: Path,
    workspace: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec_path, schema_path = workspace
    checks: list[str] = []

    def fake_symbolic_verify(
        atom: PropertyAtom,
        schema_path_arg: str,
        prior_atoms: list[PropertyAtom] | None = None,
    ) -> None:
        _ = schema_path_arg, prior_atoms
        checks.append(atom.action)
        atom.symbolic_verified = True
        atom.symbolic_verification_log = [f"checked action {atom.action}"]

    monkeypatch.setattr("autocedar.pipeline.symbolic_verify_atom", fake_symbolic_verify)

    def review_with_edit(atom: object) -> object:
        assert isinstance(atom, PropertyAtom)
        edited = replace(atom, action="view")
        return SimpleNamespace(
            atom=edited,
            decision=AtomDecision(
                atom_name=edited.name,
                action="approve",
                intent_acknowledged_by_user=True,
                edit_delta={"edits": [{"field": "action", "old": "read", "new": "view"}]},
            ),
        )

    author(
        spec_path=spec_path,
        output_dir=tmp_path / "out",
        session_id="edited-prop",
        propose_property_atoms=lambda spec_text, schema_path_arg: [_owner_only_ceiling()],
        review_atom=review_with_edit,
        synthesize=_synthesize_stub,
        schema_path_override=str(schema_path),
    )

    assert checks == ["read", "view"]
    logs = json.loads(
        (tmp_path / "out" / "edited-prop" / "stage2" / "symbolic_verification_logs.json").read_text(),
    )
    assert logs["owner_only_read"] == ["checked action view"]


# ---------------------------------------------------------------------------
# Acceptance criterion 9 — corpus logging shape.
# ---------------------------------------------------------------------------

@requires_solvers
def test_pipeline_logs_intent_and_symbolic_separately(
    tmp_path: Path, workspace: tuple[Path, Path],
) -> None:
    """The Stage 2 decisions.json must distinguish
    intent_acknowledged_by_user from symbolic_verified per §1.4."""
    spec_path, schema_path = workspace
    output_dir = tmp_path / "out"

    def propose_property_atoms(spec_text: str, schema_path_arg: str) -> list[PropertyAtom]:
        return [_owner_only_ceiling()]

    author(
        spec_path=spec_path,
        output_dir=output_dir,
        session_id="t2",
        propose_property_atoms=propose_property_atoms,
        review_atom=_approve,
        synthesize=_synthesize_stub,
        schema_path_override=str(schema_path),
    )

    decisions = json.loads(
        (output_dir / "t2" / "stage2" / "decisions.json").read_text(),
    )
    assert len(decisions) == 1
    d = decisions[0]
    assert "intent_acknowledged_by_user" in d
    assert "symbolic_verified" in d
    # Auto-approve reviewer sets intent_acknowledged_by_user=True;
    # symbolic_verified mirrors the actual symcc result.
    assert d["intent_acknowledged_by_user"] is True
    assert d["symbolic_verified"] is True  # owner-only ceiling passes all four checks


@requires_solvers
def test_pipeline_logs_prose_excerpt_attribution_per_atom(
    tmp_path: Path, workspace: tuple[Path, Path],
) -> None:
    """Every atom must have a corresponding entry in the
    attribution_decisions.json log per §9.1."""
    spec_path, schema_path = workspace
    output_dir = tmp_path / "out"

    def propose_property_atoms(spec_text: str, schema_path_arg: str) -> list[PropertyAtom]:
        return [_owner_only_ceiling(), _owner_must_floor()]

    author(
        spec_path=spec_path,
        output_dir=output_dir,
        session_id="t3",
        propose_property_atoms=propose_property_atoms,
        review_atom=_approve,
        synthesize=_synthesize_stub,
        schema_path_override=str(schema_path),
    )

    attributions = json.loads(
        (output_dir / "t3" / "stage2" / "attribution_decisions.json").read_text(),
    )
    assert len(attributions) == 2
    names = {a["atom_name"] for a in attributions}
    assert names == {"owner_only_read", "owner_must_read"}
    # Each entry has the span_text that was attached as source_excerpt.
    for a in attributions:
        assert a["span_text"] == "Owners can read their own resources."


@requires_solvers
def test_pipeline_logs_stage3_critic_score_distinct_from_verifier(
    tmp_path: Path, workspace: tuple[Path, Path],
) -> None:
    """§9.1: per-iteration verifier feedback and critic score must
    appear in separate JSON files."""
    spec_path, schema_path = workspace
    output_dir = tmp_path / "out"

    def propose_property_atoms(spec_text: str, schema_path_arg: str) -> list[PropertyAtom]:
        return [_owner_only_ceiling()]

    author(
        spec_path=spec_path,
        output_dir=output_dir,
        session_id="t4",
        propose_property_atoms=propose_property_atoms,
        review_atom=_approve,
        synthesize=_synthesize_stub,
        schema_path_override=str(schema_path),
    )

    iter1 = output_dir / "t4" / "stage3" / "iterations" / "iter_1"
    assert (iter1 / "verifier_feedback.json").exists()
    assert (iter1 / "critic_score.json").exists()
    critic = json.loads((iter1 / "critic_score.json").read_text())
    # Stub critic returns 4s across the four dimensions.
    assert all(critic[d] == 4 for d in ("idiomatic", "minimal", "attribute_prefer", "maintainable"))


@requires_solvers
def test_pipeline_returns_unsat_when_atoms_are_jointly_inconsistent(
    tmp_path: Path, workspace: tuple[Path, Path],
) -> None:
    """Stage 1.75 catches inconsistency before Stage 3 runs."""
    spec_path, schema_path = workspace
    output_dir = tmp_path / "out"

    # Owner-only ceiling combined with admin-must-read floor → unsat.
    bad_floor = PropertyAtom(
        name="admin_must_read",
        rationale="...",
        plain_english_summary="Admins must read",
        source_excerpt="...",
        constraint_type="floor",
        action="read",
        principal_types=["User"],
        resource_types=["Resource"],
        reference_cedar=(
            'permit (principal is User, action == Action::"read", resource is Resource)\n'
            "when { principal.isAdmin };\n"
        ),
    )

    def propose_property_atoms(spec_text: str, schema_path_arg: str) -> list[PropertyAtom]:
        return [_owner_only_ceiling(), bad_floor]

    result = author(
        spec_path=spec_path,
        output_dir=output_dir,
        session_id="t5",
        propose_property_atoms=propose_property_atoms,
        review_atom=_approve,
        synthesize=_synthesize_stub,
        schema_path_override=str(schema_path),
    )

    assert result.final_user_approved is False
    assert any("unsat" in note.lower() for note in result.notes)
    unsat = json.loads(
        (output_dir / "t5" / "stage1_75" / "unsat_core.json").read_text(),
    )
    assert unsat["unsat"] is True
