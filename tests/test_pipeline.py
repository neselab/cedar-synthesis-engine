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

from autocedar.atoms import ActionAtom, AttributeAtom, EntityAtom, PropertyAtom
from autocedar.atoms import RequiredSchemaSupport
from autocedar.corpus import AtomDecision
from autocedar.grounding import CEDAR_PATH, CVC5_PATH
from autocedar.pipeline import PropertyRepairPlan, author
from autocedar.ui.terminal import auto_approve

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


def _admin_credential_read_floor_with_missing_action_support() -> PropertyAtom:
    return PropertyAtom(
        name="admin_read_credential_floor",
        rationale="Administrators must be able to read credentials.",
        plain_english_summary="Administrators must be permitted to read credentials.",
        source_excerpt="Administrators can read credentials.",
        constraint_type="floor",
        action="read",
        principal_types=["Admin"],
        resource_types=["Credential"],
        reference_cedar=(
            'permit (principal is Admin, action == Action::"read", resource is Credential);'
        ),
        required_schema_support=[
            RequiredSchemaSupport(
                kind="action_principal",
                action="read",
                type_name="Admin",
                reason="The floor reference uses Admin as the requester.",
            ),
            RequiredSchemaSupport(
                kind="action_resource",
                action="read",
                type_name="Credential",
                reason="The floor reference uses Credential as the resource.",
            ),
        ],
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


def _repair_schema_plan(summary: str) -> PropertyRepairPlan:
    return PropertyRepairPlan(
        action="repair_schema",
        reason=summary,
        repair_instruction=summary,
        schema_gap_summary=summary,
    )


def test_stage1_schema_atomization_uses_source_packets_not_full_spec(tmp_path: Path) -> None:
    spec_text = textwrap.dedent("""\
        # Clinical access

        Doctors can read records for patients on their care team.

        # Patient access

        Patients can view their own records.
    """)
    spec_path = tmp_path / "policy_spec.md"
    spec_path.write_text(spec_text)
    calls: list[str] = []

    result = author(
        spec_path=spec_path,
        output_dir=tmp_path / "out",
        session_id="source-packets-stage1",
        propose_schema_atoms=lambda text: calls.append(text) or [],
        propose_property_atom=lambda spec, schema, prior, decisions: None,
        review_atom=_approve,
        synthesize=_synthesize_stub,
    )

    assert result.final_user_approved is False
    assert len(calls) == 2
    assert all("<autocedar_source_packet" in call for call in calls)
    assert all(call.strip() != spec_text.strip() for call in calls)
    session_dir = tmp_path / "out" / "source-packets-stage1"
    assert (session_dir / "stage0" / "source_index.json").exists()
    assert list((session_dir / "stage0" / "context_packets").glob("schema.*.json"))


def test_stage2_and_stage3_use_packets_and_approved_target(
    tmp_path: Path,
    workspace: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec_path, schema_path = workspace
    spec_text = textwrap.dedent("""\
        Owners can read their own resources.

        Administrators can read any resource.
    """)
    spec_path.write_text(spec_text)
    property_calls: list[str] = []

    monkeypatch.setattr(
        "autocedar.pipeline.symbolic_consistency_check",
        lambda plan, schema_path_arg: SimpleNamespace(
            tool_error=False,
            unsat=False,
            core=[],
            detail="",
        ),
    )

    result = author(
        spec_path=spec_path,
        output_dir=tmp_path / "out",
        session_id="source-packets-stage2",
        schema_path_override=str(schema_path),
        propose_property_atom=lambda spec, schema, prior, decisions: (
            property_calls.append(spec) or None
        ),
        review_atom=_approve,
        synthesize=_synthesize_stub,
    )

    # No atom was presented to a human, so successful plumbing is not semantic
    # user approval.
    assert result.final_user_approved is False
    assert len(property_calls) == 2
    assert all("<autocedar_source_packet" in call for call in property_calls)
    assert all(call.strip() != spec_text.strip() for call in property_calls)
    scenario_spec = (result.session_dir / "scenario" / "policy_spec.md").read_text()
    assert "AutoCedar Approved Intent Target" in scenario_spec
    assert "Administrators can read any resource." not in scenario_spec
    coverage = json.loads((result.session_dir / "stage0" / "coverage_ledger.json").read_text())
    assert coverage["open_property_node_ids"] == []


def test_stage0_intent_dag_records_approved_property_atoms(
    tmp_path: Path,
    workspace: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec_path, schema_path = workspace
    atom = _owner_must_floor()
    calls = [atom, _owner_only_ceiling(), None]

    def property_proposer(
        spec: str,
        schema: str,
        prior: list[PropertyAtom],
        decisions: list[AtomDecision],
    ) -> PropertyAtom | None:
        assert "<autocedar_source_packet" in spec
        _ = schema, prior, decisions
        if not calls:
            return None
        return calls.pop(0)

    def fake_symbolic_verify(
        atom_arg: PropertyAtom,
        schema_path_arg: str,
        prior_atoms: list[PropertyAtom] | None = None,
    ) -> None:
        _ = schema_path_arg, prior_atoms
        atom_arg.symbolic_verified = True
        atom_arg.symbolic_verification_log.append("stub verifier ok")

    monkeypatch.setattr("autocedar.pipeline.symbolic_verify_atom", fake_symbolic_verify)
    monkeypatch.setattr(
        "autocedar.pipeline.symbolic_consistency_check",
        lambda plan, schema_path_arg: SimpleNamespace(
            tool_error=False,
            unsat=False,
            core=[],
            detail="",
        ),
    )

    result = author(
        spec_path=spec_path,
        output_dir=tmp_path / "out",
        session_id="source-dag-with-property",
        schema_path_override=str(schema_path),
        propose_property_atom=property_proposer,
        review_atom=_approve,
        synthesize=_synthesize_stub,
    )

    dag = json.loads((result.session_dir / "stage0" / "intent_dag.json").read_text())
    assert dag["summary"]["property_atoms"] == 2
    assert any(node["id"] == "property_atom:owner_must_read" for node in dag["nodes"])
    assert any(
        edge["target"] == "property_atom:owner_must_read"
        and edge["type"] == "grounds_property_atom"
        for edge in dag["edges"]
    )
    scenario_spec = (result.session_dir / "scenario" / "policy_spec.md").read_text()
    assert "source_ids=src." in scenario_spec
    assert "owner_must_read" in scenario_spec


def test_open_source_dag_frontier_stops_before_synthesis(
    tmp_path: Path,
    workspace: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec_path, schema_path = workspace
    spec_path.write_text(
        "Owners can read their own resources."
        "Administrators can read any resource."
    )

    def fake_symbolic_verify(
        atom_arg: PropertyAtom,
        schema_path_arg: str,
        prior_atoms: list[PropertyAtom] | None = None,
    ) -> None:
        _ = schema_path_arg, prior_atoms
        atom_arg.symbolic_verified = True

    monkeypatch.setattr("autocedar.pipeline.symbolic_verify_atom", fake_symbolic_verify)

    def fail_synthesize(scenario_dir: Path) -> Path:
        _ = scenario_dir
        raise AssertionError("open source frontier must stop before Stage 3")

    result = author(
        spec_path=spec_path,
        output_dir=tmp_path / "out",
        session_id="open-frontier-stop",
        schema_path_override=str(schema_path),
        propose_property_atom=_QueuedPropertyProposer(_owner_must_floor()),
        review_atom=_approve,
        synthesize=fail_synthesize,
        max_property_proposals=1,
    )

    assert result.final_user_approved is False
    assert "remain open" in result.notes[0]
    coverage = json.loads((result.session_dir / "stage0" / "coverage_ledger.json").read_text())
    assert coverage["open_property_node_ids"]
    assert not (result.session_dir / "scenario" / "policy_spec.md").exists()


class _RecordingReviewer:
    def __init__(self) -> None:
        self.events: list[tuple[str, object]] = []

    def begin_stage(self, label: str, total: int | None) -> None:
        self.events.append(("begin", (label, total)))

    def end_stage(self, label: str, approved: int, rejected: int) -> None:
        self.events.append(("end", (label, approved, rejected)))

    def schema_ready(self, schema_text: str) -> None:
        self.events.append(("schema", schema_text))

    def property_plan_ready(self, properties: list[PropertyAtom]) -> None:
        self.events.append(("properties", len(properties)))

    def property_progress(self, payload: dict[str, object]) -> None:
        self.events.append(("progress", dict(payload)))

    def __call__(self, atom: object) -> AtomDecision:
        return _approve(atom)


class _QueuedPropertyProposer:
    def __init__(self, *atoms: PropertyAtom | list[PropertyAtom]) -> None:
        self._atoms = list(atoms)
        self.calls: list[tuple[list[str], list[str]]] = []

    def __call__(
        self,
        spec_text: str,
        schema_path_arg: str,
        prior_atoms: list[PropertyAtom],
        prior_decisions: list[AtomDecision],
    ) -> PropertyAtom | list[PropertyAtom] | None:
        _ = spec_text, schema_path_arg
        self.calls.append(
            (
                [atom.name for atom in prior_atoms],
                [decision.atom_name for decision in prior_decisions],
            ),
        )
        if not self._atoms:
            return None
        return self._atoms.pop(0)


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

    property_proposer = _QueuedPropertyProposer(_owner_only_ceiling(), _owner_must_floor())

    result = author(
        spec_path=spec_path,
        output_dir=output_dir,
        session_id="t1",
        propose_property_atom=property_proposer,
        review_atom=_approve,
        synthesize=_synthesize_stub,
        schema_path_override=str(schema_path),
    )

    assert result.session_id == "t1"
    assert result.candidate_path.exists()
    assert result.final_user_approved is True
    final_decision = json.loads(
        (result.session_dir / "stage2_5" / "final_user_decision.json").read_text(),
    )
    assert final_decision["approved"] is True

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
        "stage2/intent_graph.json",
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

    graph = json.loads((session_dir / "stage2" / "intent_graph.json").read_text())
    node_ids = {node["id"] for node in graph["nodes"]}
    assert "property:owner_only_read" in node_ids
    assert "action:read" in node_ids
    assert graph["summary"]["properties"] == 2


def test_author_emits_review_stage_and_overview_hooks(
    tmp_path: Path, workspace: tuple[Path, Path],
) -> None:
    spec_path, schema_path = workspace
    reviewer = _RecordingReviewer()

    author(
        spec_path=spec_path,
        output_dir=tmp_path / "out",
        session_id="hooks",
        propose_property_atom=_QueuedPropertyProposer(),
        review_atom=reviewer,
        synthesize=_synthesize_stub,
        schema_path_override=str(schema_path),
    )

    assert ("schema", MINIMAL_SCHEMA) in reviewer.events
    assert ("begin", ("Property intent review", None)) in reviewer.events
    assert ("end", ("Property intent review", 0, 0)) in reviewer.events
    assert ("properties", 0) in reviewer.events
    progress_events = [
        payload for kind, payload in reviewer.events if kind == "progress"
    ]
    assert any(event["event"] == "start" for event in progress_events)
    assert any(event["event"] == "source_start" for event in progress_events)
    assert any(event["event"] == "bundle_proposed" for event in progress_events)
    assert any(event["event"] == "source_complete" for event in progress_events)
    assert progress_events[-1]["event"] == "complete"


def test_stage2_reviews_bundled_properties_without_extra_planner_calls(
    tmp_path: Path,
    workspace: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec_path, schema_path = workspace

    def fake_symbolic_verify(
        atom: PropertyAtom,
        schema_path_arg: str,
        prior_atoms: list[PropertyAtom] | None = None,
    ) -> None:
        _ = schema_path_arg, prior_atoms
        atom.symbolic_verified = True
        atom.symbolic_verification_log = [f"checked {atom.name}"]

    monkeypatch.setattr("autocedar.pipeline.symbolic_verify_atom", fake_symbolic_verify)
    monkeypatch.setattr(
        "autocedar.pipeline.symbolic_consistency_check",
        lambda *args, **kwargs: SimpleNamespace(
            unsat=False,
            core=[],
            detail="",
            tool_error=False,
        ),
    )

    proposer = _QueuedPropertyProposer([_owner_must_floor(), _owner_only_ceiling()])

    author(
        spec_path=spec_path,
        output_dir=tmp_path / "out",
        session_id="bundled-stage2",
        propose_property_atom=proposer,
        review_atom=_approve,
        synthesize=_synthesize_stub,
        schema_path_override=str(schema_path),
    )

    assert proposer.calls == [([], [])]


def test_stage2_does_not_complete_source_node_with_floor_only(
    tmp_path: Path,
    workspace: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec_path, schema_path = workspace

    def fake_symbolic_verify(
        atom: PropertyAtom,
        schema_path_arg: str,
        prior_atoms: list[PropertyAtom] | None = None,
    ) -> None:
        _ = schema_path_arg, prior_atoms
        atom.symbolic_verified = True
        atom.symbolic_verification_log = [f"checked {atom.name}"]

    monkeypatch.setattr("autocedar.pipeline.symbolic_verify_atom", fake_symbolic_verify)

    def fail_synthesize(scenario_dir: Path) -> Path:
        _ = scenario_dir
        raise AssertionError("floor-only coverage must not reach Stage 3")

    proposer = _QueuedPropertyProposer(_owner_must_floor())

    result = author(
        spec_path=spec_path,
        output_dir=tmp_path / "out",
        session_id="floor-only-open",
        propose_property_atom=proposer,
        review_atom=_approve,
        synthesize=fail_synthesize,
        schema_path_override=str(schema_path),
        max_property_proposals=3,
    )

    assert result.final_user_approved is False
    assert any("full source DAG" in note for note in result.notes)
    decisions = json.loads(
        (result.session_dir / "stage2" / "decisions.json").read_text(),
    )
    assert any(
        decision["atom_name"].startswith("coverage_audit_")
        and "no same-source same-action" in decision["reason"]
        for decision in decisions
    )
    coverage = json.loads((result.session_dir / "stage0" / "coverage_ledger.json").read_text())
    assert coverage["open_property_node_ids"]


def test_stage2_completes_source_node_after_floor_and_safety(
    tmp_path: Path,
    workspace: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec_path, schema_path = workspace

    def fake_symbolic_verify(
        atom: PropertyAtom,
        schema_path_arg: str,
        prior_atoms: list[PropertyAtom] | None = None,
    ) -> None:
        _ = schema_path_arg, prior_atoms
        atom.symbolic_verified = True
        atom.symbolic_verification_log = [f"checked {atom.name}"]

    monkeypatch.setattr("autocedar.pipeline.symbolic_verify_atom", fake_symbolic_verify)
    monkeypatch.setattr(
        "autocedar.pipeline.symbolic_consistency_check",
        lambda *args, **kwargs: SimpleNamespace(
            unsat=False,
            core=[],
            detail="",
            tool_error=False,
        ),
    )

    proposer = _QueuedPropertyProposer(_owner_must_floor(), _owner_only_ceiling())

    result = author(
        spec_path=spec_path,
        output_dir=tmp_path / "out",
        session_id="floor-plus-safety-complete",
        propose_property_atom=proposer,
        review_atom=_approve,
        synthesize=_synthesize_stub,
        schema_path_override=str(schema_path),
    )

    assert result.final_user_approved is True
    coverage = json.loads((result.session_dir / "stage0" / "coverage_ledger.json").read_text())
    assert coverage["open_property_node_ids"] == []
    decisions = json.loads(
        (result.session_dir / "stage2" / "decisions.json").read_text(),
    )
    assert not any(decision["atom_name"].startswith("coverage_audit_") for decision in decisions)


def test_author_stops_when_no_schema_atoms_are_approved(tmp_path: Path) -> None:
    spec_path = tmp_path / "policy_spec.md"
    spec_path.write_text("Owners can read documents.")

    result = author(
        spec_path=spec_path,
        output_dir=tmp_path / "out",
        session_id="empty-schema",
        propose_schema_atoms=lambda spec_text: [],
        propose_property_atom=_QueuedPropertyProposer(),
        review_atom=_approve,
        synthesize=_synthesize_stub,
    )

    assert result.final_user_approved is False
    assert result.candidate_path == Path("")
    assert "no approved schema atoms" in result.notes[0]
    validation = json.loads(
        (tmp_path / "out" / "empty-schema" / "stage1" / "schema_validation.json").read_text(),
    )
    assert validation[0]["validator_error"] == "no approved schema atoms"


@requires_solvers
def test_author_validates_and_fixes_composed_schema_before_stage2(tmp_path: Path) -> None:
    spec_path = tmp_path / "policy_spec.md"
    spec_path.write_text("Users can read documents.")

    atoms = [
        EntityAtom(
            name="User",
            rationale="principal",
            plain_english_summary="A user.",
            source_excerpt="Users",
        ),
        ActionAtom(
            name="read",
            rationale="read action",
            plain_english_summary="Read a document.",
            source_excerpt="read documents",
            principal_types=["User"],
            resource_types=["Document"],
        ),
    ]
    fixed_schema = textwrap.dedent("""\
        entity User;

        entity Document;

        action read appliesTo {
            principal: [User],
            resource: [Document],
        };
    """)
    schema_seen_by_stage2: list[str] = []

    result = author(
        spec_path=spec_path,
        output_dir=tmp_path / "out",
        session_id="schema-fix",
        propose_schema_atoms=lambda spec_text: atoms,
        fix_schema=lambda schema_text, cedar_error, spec_text: fixed_schema,
        propose_property_atom=lambda spec_text, schema_path_arg, prior_atoms, prior_decisions: (
            schema_seen_by_stage2.append(Path(schema_path_arg).read_text()) or None
        ),
        review_atom=_approve,
        synthesize=_synthesize_stub,
    )

    assert result.final_user_approved is True
    assert schema_seen_by_stage2 == [fixed_schema]
    validation = json.loads(
        (tmp_path / "out" / "schema-fix" / "stage1" / "schema_validation.json").read_text(),
    )
    assert len(validation) == 2
    assert validation[0]["validator_passed"] is False
    assert validation[0]["llm_was_called"] is True
    assert validation[1]["validator_passed"] is True


@requires_solvers
def test_author_repairs_rejected_schema_atom_before_composition(tmp_path: Path) -> None:
    spec_path = tmp_path / "policy_spec.md"
    spec_path.write_text("Users can read documents.")

    bad_entity = EntityAtom(
        name="Person",
        rationale="wrong principal name",
        plain_english_summary="A person.",
        source_excerpt="Users",
    )
    fixed_entity = EntityAtom(
        name="User",
        rationale="principal",
        plain_english_summary="A user.",
        source_excerpt="Users",
    )
    document = EntityAtom(
        name="Document",
        rationale="resource",
        plain_english_summary="A document.",
        source_excerpt="documents",
    )
    action = ActionAtom(
        name="read",
        rationale="read action",
        plain_english_summary="Read a document.",
        source_excerpt="read documents",
        principal_types=["User"],
        resource_types=["Document"],
    )
    reviewed: list[str] = []
    repairs: list[tuple[str, str]] = []

    def reviewer(atom: object) -> AtomDecision:
        reviewed.append(getattr(atom, "name", "?"))
        if getattr(atom, "name", "") == "Person":
            return AtomDecision(
                atom_name="Person",
                action="reject",
                reason="principal entity should be named User",
            )
        return _approve(atom)

    def repair_schema_atom(
        spec_text: str,
        rejected_atom: object,
        reason: str,
        prior_atoms: list[object],
    ) -> object:
        _ = spec_text, prior_atoms
        repairs.append((getattr(rejected_atom, "name", "?"), reason))
        return fixed_entity

    result = author(
        spec_path=spec_path,
        output_dir=tmp_path / "out",
        session_id="schema-atom-repair",
        propose_schema_atoms=lambda spec_text: [bad_entity, document, action],
        repair_schema_atom=repair_schema_atom,
        propose_property_atom=_QueuedPropertyProposer(),
        review_atom=reviewer,
        synthesize=_synthesize_stub,
    )

    assert result.final_user_approved is True
    assert reviewed == ["Person", "User", "Document", "read"]
    assert repairs == [("Person", "principal entity should be named User")]
    assert "entity User;" in result.schema_text
    assert "entity Person;" not in result.schema_text
    decisions = json.loads(
        (tmp_path / "out" / "schema-atom-repair" / "stage1" / "decisions.json").read_text(),
    )
    assert decisions[0]["atom_name"] == "User"
    assert decisions[0]["edit_delta"]["replaced_after_reject"] is True


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
        propose_property_atom=_QueuedPropertyProposer(_owner_only_ceiling()),
        review_atom=review_with_edit,
        synthesize=_synthesize_stub,
        schema_path_override=str(schema_path),
    )

    assert checks == ["read", "view"]
    logs = json.loads(
        (tmp_path / "out" / "edited-prop" / "stage2" / "symbolic_verification_logs.json").read_text(),
    )
    assert logs["owner_only_read"] == ["checked action view"]


def test_author_repairs_rejected_property_atom(
    tmp_path: Path,
    workspace: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec_path, schema_path = workspace
    reviewed: list[str] = []
    repaired: list[tuple[str, str]] = []

    def fake_symbolic_verify(
        atom: PropertyAtom,
        schema_path_arg: str,
        prior_atoms: list[PropertyAtom] | None = None,
    ) -> None:
        _ = schema_path_arg, prior_atoms
        atom.symbolic_verified = True
        atom.symbolic_verification_log = [f"checked {atom.name}"]

    monkeypatch.setattr("autocedar.pipeline.symbolic_verify_atom", fake_symbolic_verify)

    replacement = _owner_must_floor()

    def review_then_approve(atom: object) -> AtomDecision:
        reviewed.append(getattr(atom, "name", "?"))
        if len(reviewed) == 1:
            return AtomDecision(
                atom_name=getattr(atom, "name", "?"),
                action="reject",
                reason="floor conflicts with prior ceiling",
            )
        return AtomDecision(
            atom_name=getattr(atom, "name", "?"),
            action="approve",
            intent_acknowledged_by_user=True,
        )

    def repair_property_atom(
        spec_text: str,
        schema_path_arg: str,
        rejected_atom: PropertyAtom,
        reason: str,
        prior_atoms: list[PropertyAtom],
    ) -> PropertyAtom:
        _ = spec_text, schema_path_arg, prior_atoms
        repaired.append((rejected_atom.name, reason))
        return replacement

    def repair_planner(*args, **kwargs) -> PropertyRepairPlan:
        _ = args, kwargs
        return PropertyRepairPlan(
            action="repair_current_property",
            reason="repair current property",
            repair_instruction="floor conflicts with prior ceiling",
        )

    author(
        spec_path=spec_path,
        output_dir=tmp_path / "out",
        session_id="repaired-prop",
        propose_property_atom=_QueuedPropertyProposer(
            _owner_only_ceiling(),
            _owner_only_ceiling(),
        ),
        plan_property_repair=repair_planner,
        repair_property_atom=repair_property_atom,
        review_atom=review_then_approve,
        synthesize=_synthesize_stub,
        schema_path_override=str(schema_path),
    )

    assert reviewed == ["owner_only_read", "owner_must_read", "owner_only_read"]
    assert repaired == [("owner_only_read", "floor conflicts with prior ceiling")]
    decisions = json.loads(
        (tmp_path / "out" / "repaired-prop" / "stage2" / "decisions.json").read_text(),
    )
    assert len(decisions) == 2
    assert decisions[0]["action"] == "approve"
    assert decisions[0]["atom_name"] == "owner_must_read"
    assert decisions[0]["edit_delta"]["replaced_after_reject"] is True
    assert decisions[0]["edit_delta"]["reject_history"][0]["atom_name"] == "owner_only_read"
    assert decisions[1]["action"] == "approve"
    assert decisions[1]["atom_name"] == "owner_only_read"


def test_author_skips_later_property_duplicate_after_repair(
    tmp_path: Path,
    workspace: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec_path, schema_path = workspace
    reviewed: list[str] = []

    def fake_symbolic_verify(
        atom: PropertyAtom,
        schema_path_arg: str,
        prior_atoms: list[PropertyAtom] | None = None,
    ) -> None:
        _ = schema_path_arg, prior_atoms
        atom.symbolic_verified = True
        atom.symbolic_verification_log = [f"checked {atom.name}"]

    monkeypatch.setattr("autocedar.pipeline.symbolic_verify_atom", fake_symbolic_verify)

    weak_ceiling = _owner_only_ceiling()
    strong_ceiling = replace(
        weak_ceiling,
        reference_cedar=(
            'permit (principal is User, action == Action::"read", resource is Resource)\n'
            "when { principal == resource.owner && principal.isAdmin };\n"
        ),
        plain_english_summary="Only admin owners can read.",
    )
    bad_floor = _owner_must_floor()

    def review_then_approve(atom: object) -> AtomDecision:
        reviewed.append(getattr(atom, "name", "?"))
        if getattr(atom, "name", "?") == "owner_must_read":
            return AtomDecision(
                atom_name="owner_must_read",
                action="reject",
                reason="must be a stricter ceiling instead",
            )
        return _approve(atom)

    def repair_property_atom(
        spec_text: str,
        schema_path_arg: str,
        rejected_atom: PropertyAtom,
        reason: str,
        prior_atoms: list[PropertyAtom],
    ) -> PropertyAtom:
        _ = spec_text, schema_path_arg, rejected_atom, reason, prior_atoms
        return strong_ceiling

    author(
        spec_path=spec_path,
        output_dir=tmp_path / "out",
        session_id="duplicate-after-repair",
        propose_property_atom=_QueuedPropertyProposer(bad_floor, weak_ceiling),
        repair_property_atom=repair_property_atom,
        review_atom=review_then_approve,
        synthesize=_synthesize_stub,
        schema_path_override=str(schema_path),
    )

    assert reviewed == ["owner_must_read", "owner_only_read"]
    decisions = json.loads(
        (tmp_path / "out" / "duplicate-after-repair" / "stage2" / "decisions.json").read_text(),
    )
    assert [decision["action"] for decision in decisions] == ["approve", "reject"]
    assert decisions[1]["reason"].startswith("Duplicate property atom name")
    ref = (
        tmp_path
        / "out"
        / "duplicate-after-repair"
        / "stage2"
        / "final_plan"
        / "references"
        / "owner_only_read.cedar"
    ).read_text()
    assert "principal.isAdmin" in ref


def test_author_uses_repairer_selected_direction_for_property_repair(
    tmp_path: Path,
    workspace: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec_path, schema_path = workspace

    def fake_symbolic_verify(
        atom: PropertyAtom,
        schema_path_arg: str,
        prior_atoms: list[PropertyAtom] | None = None,
    ) -> None:
        _ = schema_path_arg, prior_atoms
        atom.symbolic_verified = True
        atom.symbolic_verification_log = [f"checked {atom.name}"]

    monkeypatch.setattr("autocedar.pipeline.symbolic_verify_atom", fake_symbolic_verify)

    bad_floor = _owner_must_floor()
    model_returned_ceiling = replace(
        _owner_only_ceiling(),
        name="owner_read_repaired_ceiling",
        reference_cedar=(
            'permit (principal is User, action == Action::"read", resource is Resource)\n'
            "when { principal == resource.owner && principal.isAdmin };\n"
        ),
    )
    reviewed: list[tuple[str, str]] = []

    def review_then_approve(atom: object) -> AtomDecision:
        reviewed.append((getattr(atom, "name", "?"), getattr(atom, "constraint_type", "")))
        if len(reviewed) == 1:
            return AtomDecision(
                atom_name=getattr(atom, "name", "?"),
                action="reject",
                reason="missing admin condition",
            )
        return _approve(atom)

    author(
        spec_path=spec_path,
        output_dir=tmp_path / "out",
        session_id="model-selected-direction-repair",
        propose_property_atom=_QueuedPropertyProposer(bad_floor),
        plan_property_repair=lambda *args, **kwargs: PropertyRepairPlan(
            action="repair_current_property",
            reason="repair the current property",
            repair_instruction="repair the current property",
        ),
        repair_property_atom=lambda *args: model_returned_ceiling,
        review_atom=review_then_approve,
        synthesize=_synthesize_stub,
        schema_path_override=str(schema_path),
    )

    assert reviewed == [
        ("owner_must_read", "floor"),
        ("owner_read_repaired_ceiling", "ceiling"),
    ]
    plan_py = (
        tmp_path
        / "out"
        / "model-selected-direction-repair"
        / "stage2"
        / "final_plan"
        / "verification_plan.py"
    ).read_text()
    assert '"type": "implies"' in plan_py
    assert "owner_read_repaired_ceiling" in plan_py


def test_author_allows_explicit_property_direction_change(
    tmp_path: Path,
    workspace: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec_path, schema_path = workspace

    def fake_symbolic_verify(
        atom: PropertyAtom,
        schema_path_arg: str,
        prior_atoms: list[PropertyAtom] | None = None,
    ) -> None:
        _ = schema_path_arg, prior_atoms
        atom.symbolic_verified = True
        atom.symbolic_verification_log = [f"checked {atom.name}"]

    monkeypatch.setattr("autocedar.pipeline.symbolic_verify_atom", fake_symbolic_verify)

    bad_floor = _owner_must_floor()
    ceiling = replace(_owner_only_ceiling(), name="owner_repaired_ceiling")
    reviewed: list[tuple[str, str]] = []

    def review_then_approve(atom: object) -> AtomDecision:
        reviewed.append((getattr(atom, "name", "?"), getattr(atom, "constraint_type", "")))
        if len(reviewed) == 1:
            return AtomDecision(
                atom_name=getattr(atom, "name", "?"),
                action="reject",
                reason="wrong direction; this should be a ceiling instead",
            )
        return _approve(atom)

    author(
        spec_path=spec_path,
        output_dir=tmp_path / "out",
        session_id="allow-direction-change",
        propose_property_atom=_QueuedPropertyProposer(bad_floor),
        plan_property_repair=lambda *args, **kwargs: PropertyRepairPlan(
            action="repair_current_property",
            reason="repair the current property",
            repair_instruction="repair the current property",
        ),
        repair_property_atom=lambda *args: ceiling,
        review_atom=review_then_approve,
        synthesize=_synthesize_stub,
        schema_path_override=str(schema_path),
    )

    assert reviewed == [
        ("owner_must_read", "floor"),
        ("owner_repaired_ceiling", "ceiling"),
    ]


def test_hitl_schema_gap_rejection_repairs_schema_and_continues(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec_path = tmp_path / "policy_spec.md"
    spec_path.write_text("Students can register for current course offerings.")

    def fake_symbolic_verify(
        atom: PropertyAtom,
        schema_path_arg: str,
        prior_atoms: list[PropertyAtom] | None = None,
    ) -> None:
        _ = schema_path_arg, prior_atoms
        atom.symbolic_verified = True
        atom.symbolic_verification_log = [f"checked {atom.name}"]

    user = EntityAtom(
        name="Student",
        rationale="student principal",
        plain_english_summary="A student.",
        source_excerpt="Students",
    )
    offering = EntityAtom(
        name="CourseOffering",
        rationale="course offering resource",
        plain_english_summary="A course offering.",
        source_excerpt="course offerings",
    )
    register = ActionAtom(
        name="register",
        rationale="registration action",
        plain_english_summary="Register for an offering.",
        source_excerpt="register",
        principal_types=["Student"],
        resource_types=["CourseOffering"],
    )
    is_current = AttributeAtom(
        name="course_offering_is_current",
        rationale="current semester marker",
        plain_english_summary="Marks a course offering as current.",
        source_excerpt="current course offerings",
        on_entity="CourseOffering",
        field_name="isCurrent",
        cedar_type="Bool",
    )
    weak_property = PropertyAtom(
        name="student_register_floor_weak",
        rationale="registration floor without current-semester boundary",
        plain_english_summary="Students can register for course offerings.",
        source_excerpt="Students can register for current course offerings.",
        constraint_type="floor",
        action="register",
        principal_types=["Student"],
        resource_types=["CourseOffering"],
        reference_cedar='permit (principal, action == Action::"register", resource);',
    )
    repaired_property = replace(
        weak_property,
        name="student_register_current_floor",
        plain_english_summary="Students can register for current course offerings.",
        reference_cedar=(
            'permit (principal, action == Action::"register", resource) '
            "when { resource.isCurrent };"
        ),
    )
    current_ceiling = replace(
        repaired_property,
        name="student_register_current_ceiling",
        constraint_type="ceiling",
    )
    schema_calls = 0
    schema_seen_by_property: list[str] = []
    properties = [weak_property, repaired_property, current_ceiling]
    synth_called = False

    def schema_proposer(text: str) -> list[object]:
        nonlocal schema_calls
        schema_calls += 1
        if schema_calls == 1:
            return [user, offering, register]
        assert "<schema_gap_repair>" in text
        return [is_current]

    def property_proposer(
        text: str,
        schema_path_arg: str,
        prior_atoms: list[PropertyAtom],
        prior_decisions: list[AtomDecision],
    ) -> PropertyAtom | None:
        _ = text, prior_atoms, prior_decisions
        schema_seen_by_property.append(Path(schema_path_arg).read_text())
        if not properties:
            return None
        return properties.pop(0)

    def reviewer(atom: object) -> AtomDecision:
        if not isinstance(atom, PropertyAtom):
            return _approve(atom)
        if atom.name == "student_register_floor_weak":
            return AtomDecision(
                atom_name=atom.name,
                action="reject",
                reason="schema needs a current-semester field before this property is acceptable",
            )
        return _approve(atom)

    def fake_compose_and_validate(draft, schema_path_arg, llm=None, spec_text="", max_attempts=3):
        from autocedar.schema_atomizer import FixAttempt, compose_schema

        _ = llm, spec_text, max_attempts
        schema_text = compose_schema(draft)
        schema_path_arg.write_text(schema_text)
        return SimpleNamespace(
            schema_text=schema_text,
            schema_path=schema_path_arg,
            succeeded=True,
            attempts=[
                FixAttempt(
                    attempt_number=1,
                    schema_text=schema_text,
                    validator_passed=True,
                ),
            ],
        )

    def synthesize(scenario_dir: Path) -> Path:
        nonlocal synth_called
        synth_called = True
        return _synthesize_stub(scenario_dir)

    monkeypatch.setattr("autocedar.pipeline.symbolic_verify_atom", fake_symbolic_verify)
    monkeypatch.setattr("autocedar.pipeline.compose_and_validate", fake_compose_and_validate)
    monkeypatch.setattr(
        "autocedar.pipeline.symbolic_consistency_check",
        lambda *args, **kwargs: SimpleNamespace(
            unsat=False,
            core=[],
            detail="",
            tool_error=False,
        ),
    )

    result = author(
        spec_path=spec_path,
        output_dir=tmp_path / "out",
        session_id="schema-gap-repair",
        propose_schema_atoms=schema_proposer,
        propose_property_atom=property_proposer,
        plan_property_repair=lambda *args, **kwargs: _repair_schema_plan(
            "add current-semester support to the schema",
        ),
        review_atom=reviewer,
        synthesize=synthesize,
    )

    assert result.final_user_approved is True
    assert result.candidate_path.exists()
    assert synth_called is True
    assert schema_calls == 2
    assert "isCurrent: Bool" not in schema_seen_by_property[0]
    assert "isCurrent: Bool" in schema_seen_by_property[1]
    assert "isCurrent: Bool" in result.schema_text

    session_dir = tmp_path / "out" / "schema-gap-repair"
    gaps = json.loads((session_dir / "stage1_5" / "schema_gaps.json").read_text())
    assert gaps[0]["atom_name"] == "student_register_floor_weak"
    repairs = json.loads((session_dir / "stage1_5" / "schema_gap_repairs.json").read_text())
    assert repairs[0]["approved_atoms"][0]["field_name"] == "isCurrent"
    assert (session_dir / "stage2" / "final_plan" / "verification_plan.py").exists()
    assert (session_dir / "stage3" / "final_candidate.cedar").exists()


def test_batch_auto_approval_advances_without_human_semantic_approval(
    tmp_path: Path,
    workspace: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Batch plumbing can synthesize, but it cannot manufacture HITL evidence."""

    spec_path, schema_path = workspace

    def fake_symbolic_verify(
        atom: PropertyAtom,
        schema_path_arg: str,
        prior_atoms: list[PropertyAtom] | None = None,
    ) -> None:
        _ = schema_path_arg, prior_atoms
        atom.symbolic_verified = True
        atom.symbolic_verification_log = ["symbolic checks passed"]

    monkeypatch.setattr("autocedar.pipeline.cedar_validate_schema", lambda path: (True, ""))
    monkeypatch.setattr("autocedar.pipeline.symbolic_verify_atom", fake_symbolic_verify)
    monkeypatch.setattr(
        "autocedar.pipeline.symbolic_consistency_check",
        lambda *args, **kwargs: SimpleNamespace(
            unsat=False,
            core=[],
            detail="",
            tool_error=False,
        ),
    )

    result = author(
        spec_path=spec_path,
        output_dir=tmp_path / "out",
        session_id="batch-plumbing-only",
        propose_property_atom=_QueuedPropertyProposer(_owner_only_ceiling()),
        review_atom=auto_approve,
        synthesize=_synthesize_stub,
        schema_path_override=str(schema_path),
        run_incremental_checks=False,
    )

    assert result.candidate_path.exists()
    assert result.final_user_approved is False
    assert result.plan.properties[0].intent_acknowledged_by_user is False

    decision = json.loads(
        (result.session_dir / "stage2" / "decisions.json").read_text(),
    )[0]
    assert decision["action"] == "approve"
    assert decision["symbolic_verified"] is True
    assert decision["intent_acknowledged_by_user"] is False

    final_decision = json.loads(
        (result.session_dir / "stage2_5" / "final_user_decision.json").read_text(),
    )
    assert final_decision["approved"] is False
    assert "plumbing-only approvals" in final_decision["reason"]


def test_schema_gap_repair_patches_supplied_schema_without_llm_rewrite(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec_path = tmp_path / "policy_spec.md"
    spec_path.write_text("Students can register for current course offerings.")
    schema_path = tmp_path / "schema.cedarschema"
    schema_path.write_text(textwrap.dedent("""\
        entity Student;

        entity CourseOffering;

        action register appliesTo {
            principal: [Student],
            resource: [CourseOffering],
        };
    """))

    weak_property = PropertyAtom(
        name="student_register_floor_weak",
        rationale="registration floor without current-semester boundary",
        plain_english_summary="Students can register for course offerings.",
        source_excerpt="Students can register for current course offerings.",
        constraint_type="floor",
        action="register",
        principal_types=["Student"],
        resource_types=["CourseOffering"],
        reference_cedar='permit (principal, action == Action::"register", resource);',
    )
    repaired_property = replace(
        weak_property,
        name="student_register_current_floor",
        reference_cedar=(
            'permit (principal, action == Action::"register", resource) '
            "when { resource.isCurrent };"
        ),
    )
    current_ceiling = replace(
        repaired_property,
        name="student_register_current_ceiling",
        constraint_type="ceiling",
    )
    is_current = AttributeAtom(
        name="course_offering_is_current",
        rationale="current semester marker",
        plain_english_summary="Marks a course offering as current.",
        source_excerpt="current course offerings",
        on_entity="CourseOffering",
        field_name="isCurrent",
        cedar_type="Bool",
    )
    properties = [weak_property, repaired_property, current_ceiling]
    schemas_seen: list[str] = []

    def fake_symbolic_verify(
        atom: PropertyAtom,
        schema_path_arg: str,
        prior_atoms: list[PropertyAtom] | None = None,
    ) -> None:
        _ = schema_path_arg, prior_atoms
        atom.symbolic_verified = True
        atom.symbolic_verification_log = [f"checked {atom.name}"]

    def property_proposer(
        text: str,
        schema_path_arg: str,
        prior_atoms: list[PropertyAtom],
        prior_decisions: list[AtomDecision],
    ) -> PropertyAtom | None:
        _ = text, prior_atoms, prior_decisions
        schemas_seen.append(Path(schema_path_arg).read_text())
        if not properties:
            return None
        return properties.pop(0)

    def reviewer(atom: object) -> AtomDecision:
        if not isinstance(atom, PropertyAtom):
            return _approve(atom)
        if atom.name == "student_register_floor_weak":
            return AtomDecision(
                atom_name=atom.name,
                action="reject",
                reason="schema needs a current-semester field before this property is acceptable",
            )
        return _approve(atom)

    def fail_schema_rewrite(schema_text: str, cedar_error: str, text: str) -> str:
        _ = schema_text, cedar_error, text
        raise AssertionError("supplied-schema repair must not ask the LLM to rewrite schema text")

    monkeypatch.setattr("autocedar.pipeline.symbolic_verify_atom", fake_symbolic_verify)
    monkeypatch.setattr("autocedar.pipeline.cedar_validate_schema", lambda path: (True, ""))
    monkeypatch.setattr(
        "autocedar.pipeline.symbolic_consistency_check",
        lambda *args, **kwargs: SimpleNamespace(
            unsat=False,
            core=[],
            detail="",
            tool_error=False,
        ),
    )

    result = author(
        spec_path=spec_path,
        output_dir=tmp_path / "out",
        session_id="schema-override-repair",
        propose_schema_atoms=lambda text: [is_current],
        fix_schema=fail_schema_rewrite,
        propose_property_atom=property_proposer,
        plan_property_repair=lambda *args, **kwargs: _repair_schema_plan(
            "add current-semester support to the supplied schema",
        ),
        review_atom=reviewer,
        synthesize=_synthesize_stub,
        schema_path_override=str(schema_path),
    )

    assert result.final_user_approved is True
    assert "isCurrent: Bool" not in schemas_seen[0]
    assert "isCurrent: Bool" in schemas_seen[1]
    repairs = json.loads(
        (tmp_path / "out" / "schema-override-repair" / "stage1_5" / "schema_gap_repairs.json")
        .read_text(),
    )
    assert repairs[0]["schema_validation"][0]["llm_was_called"] is False


def test_schema_gap_repairs_log_all_repair_records(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec_path = tmp_path / "policy_spec.md"
    spec_path.write_text("Students can register for current and upcoming course offerings.")

    student = EntityAtom(
        name="Student",
        rationale="student principal",
        plain_english_summary="A student.",
        source_excerpt="Students",
    )
    offering = EntityAtom(
        name="CourseOffering",
        rationale="course offering",
        plain_english_summary="A course offering.",
        source_excerpt="course offerings",
    )
    register = ActionAtom(
        name="register",
        rationale="register action",
        plain_english_summary="Register.",
        source_excerpt="register",
        principal_types=["Student"],
        resource_types=["CourseOffering"],
    )
    current_attr = AttributeAtom(
        name="course_offering_is_current",
        rationale="current marker",
        plain_english_summary="Current marker.",
        source_excerpt="current",
        on_entity="CourseOffering",
        field_name="isCurrent",
        cedar_type="Bool",
    )
    upcoming_attr = AttributeAtom(
        name="course_offering_is_upcoming",
        rationale="upcoming marker",
        plain_english_summary="Upcoming marker.",
        source_excerpt="upcoming",
        on_entity="CourseOffering",
        field_name="isUpcoming",
        cedar_type="Bool",
    )
    weak_current = PropertyAtom(
        name="weak_current",
        rationale="missing current field",
        plain_english_summary="Current registration.",
        source_excerpt="current offerings",
        constraint_type="floor",
        action="register",
        principal_types=["Student"],
        resource_types=["CourseOffering"],
        reference_cedar='permit (principal, action == Action::"register", resource);',
    )
    current_ok = replace(
        weak_current,
        name="current_ok",
        reference_cedar='permit (principal, action == Action::"register", resource) when { resource.isCurrent };',
    )
    current_ceiling = replace(current_ok, name="current_ceiling", constraint_type="ceiling")
    weak_upcoming = replace(weak_current, name="weak_upcoming", source_excerpt="upcoming offerings")
    upcoming_ok = replace(
        weak_current,
        name="upcoming_ok",
        reference_cedar='permit (principal, action == Action::"register", resource) when { resource.isUpcoming };',
    )
    upcoming_ceiling = replace(upcoming_ok, name="upcoming_ceiling", constraint_type="ceiling")
    property_queue = [
        weak_current,
        current_ok,
        current_ceiling,
        weak_upcoming,
        upcoming_ok,
        upcoming_ceiling,
    ]
    schema_calls = 0

    def schema_proposer(text: str) -> list[object]:
        nonlocal schema_calls
        schema_calls += 1
        if schema_calls == 1:
            return [student, offering, register]
        if schema_calls == 2:
            return [current_attr]
        return [upcoming_attr]

    def property_proposer(
        text: str,
        schema_path_arg: str,
        prior_atoms: list[PropertyAtom],
        prior_decisions: list[AtomDecision],
    ) -> PropertyAtom | None:
        _ = text, schema_path_arg, prior_atoms, prior_decisions
        if not property_queue:
            return None
        return property_queue.pop(0)

    def reviewer(atom: object) -> AtomDecision:
        if not isinstance(atom, PropertyAtom):
            return _approve(atom)
        if atom.name == "weak_current":
            return AtomDecision(atom_name=atom.name, action="reject", reason="schema needs current marker")
        if atom.name == "weak_upcoming":
            return AtomDecision(atom_name=atom.name, action="reject", reason="schema needs upcoming marker")
        return _approve(atom)

    def fake_compose_and_validate(draft, schema_path_arg, llm=None, spec_text="", max_attempts=3):
        from autocedar.schema_atomizer import FixAttempt, compose_schema

        _ = llm, spec_text, max_attempts
        schema_text = compose_schema(draft)
        schema_path_arg.write_text(schema_text)
        return SimpleNamespace(
            schema_text=schema_text,
            schema_path=schema_path_arg,
            succeeded=True,
            attempts=[FixAttempt(attempt_number=1, schema_text=schema_text, validator_passed=True)],
        )

    monkeypatch.setattr("autocedar.pipeline.compose_and_validate", fake_compose_and_validate)
    monkeypatch.setattr(
        "autocedar.pipeline.symbolic_verify_atom",
        lambda atom, schema_path_arg, prior_atoms=None: setattr(atom, "symbolic_verified", True),
    )
    monkeypatch.setattr(
        "autocedar.pipeline.symbolic_consistency_check",
        lambda *args, **kwargs: SimpleNamespace(
            unsat=False,
            core=[],
            detail="",
            tool_error=False,
        ),
    )

    result = author(
        spec_path=spec_path,
        output_dir=tmp_path / "out",
        session_id="schema-repair-log-all",
        propose_schema_atoms=schema_proposer,
        propose_property_atom=property_proposer,
        plan_property_repair=lambda *args, **kwargs: _repair_schema_plan(
            "add the missing lifecycle marker to the schema",
        ),
        review_atom=reviewer,
        synthesize=_synthesize_stub,
    )

    assert result.final_user_approved is True
    repairs = json.loads(
        (tmp_path / "out" / "schema-repair-log-all" / "stage1_5" / "schema_gap_repairs.json")
        .read_text(),
    )
    assert [record["gap"]["atom_name"] for record in repairs] == ["weak_current", "weak_upcoming"]
    assert [record["approved_atoms"][0]["field_name"] for record in repairs] == [
        "isCurrent",
        "isUpcoming",
    ]


def test_rejecting_consistency_failure_can_repair_prior_property(
    tmp_path: Path,
    workspace: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec_path, schema_path = workspace
    broad_floor = PropertyAtom(
        name="owner_read_floor",
        rationale="owner floor without admin boundary",
        plain_english_summary="Owners can read.",
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
    strict_ceiling = PropertyAtom(
        name="owner_admin_read_ceiling",
        rationale="only admin owners can read",
        plain_english_summary="Only admin owners can read.",
        source_excerpt="Only admin owners can read their own resources.",
        constraint_type="ceiling",
        action="read",
        principal_types=["User"],
        resource_types=["Resource"],
        reference_cedar=(
            'permit (principal is User, action == Action::"read", resource is Resource)\n'
            "when { principal == resource.owner && principal.isAdmin };\n"
        ),
    )
    repaired_floor = replace(
        broad_floor,
        reference_cedar=(
            'permit (principal is User, action == Action::"read", resource is Resource)\n'
            "when { principal == resource.owner && principal.isAdmin };\n"
        ),
    )
    reviewed: list[str] = []
    repaired: list[str] = []

    def fake_symbolic_verify(
        atom: PropertyAtom,
        schema_path_arg: str,
        prior_atoms: list[PropertyAtom] | None = None,
    ) -> None:
        _ = schema_path_arg
        prior_atoms = prior_atoms or []
        atom.symbolic_verified = True
        if atom.name == strict_ceiling.name and any(
            prior.name == broad_floor.name and "isAdmin" not in prior.reference_cedar
            for prior in prior_atoms
        ):
            atom.symbolic_verified = False
            atom.symbolic_verification_log = [
                "Consistency check failed against `owner_read_floor`: "
                "floor owner_read_floor not contained in ceiling owner_admin_read_ceiling",
            ]
        else:
            atom.symbolic_verification_log = [f"checked {atom.name}"]

    def reviewer(atom: object) -> AtomDecision:
        name = getattr(atom, "name", "?")
        reviewed.append(name)
        if name == strict_ceiling.name and len([n for n in reviewed if n == strict_ceiling.name]) == 1:
            return AtomDecision(
                atom_name=name,
                action="reject",
                reason="prior floor too broad; repair the floor to include the admin boundary",
            )
        return _approve(atom)

    def repair_property_atom(
        spec_text: str,
        schema_path_arg: str,
        rejected_atom: PropertyAtom,
        reason: str,
        prior_atoms: list[PropertyAtom],
    ) -> PropertyAtom:
        _ = spec_text, schema_path_arg, reason, prior_atoms
        repaired.append(rejected_atom.name)
        assert rejected_atom.name == broad_floor.name
        return repaired_floor

    def repair_planner(*args, **kwargs) -> PropertyRepairPlan:
        _ = args, kwargs
        return PropertyRepairPlan(
            action="repair_prior_property",
            target_atom=broad_floor.name,
            reason="repair prior floor",
            repair_instruction="repair the floor to include the admin boundary",
        )

    monkeypatch.setattr("autocedar.pipeline.symbolic_verify_atom", fake_symbolic_verify)
    monkeypatch.setattr(
        "autocedar.pipeline.symbolic_consistency_check",
        lambda *args, **kwargs: SimpleNamespace(
            unsat=False,
            core=[],
            detail="",
            tool_error=False,
        ),
    )

    result = author(
        spec_path=spec_path,
        output_dir=tmp_path / "out",
        session_id="repair-prior-property",
        propose_property_atom=_QueuedPropertyProposer(broad_floor, strict_ceiling),
        plan_property_repair=repair_planner,
        repair_property_atom=repair_property_atom,
        review_atom=reviewer,
        synthesize=_synthesize_stub,
        schema_path_override=str(schema_path),
    )

    assert result.final_user_approved is True
    assert repaired == [broad_floor.name]
    assert reviewed == [
        broad_floor.name,
        strict_ceiling.name,
        broad_floor.name,
        strict_ceiling.name,
    ]
    assert result.plan.properties[0].reference_cedar == repaired_floor.reference_cedar
    decisions = json.loads(
        (tmp_path / "out" / "repair-prior-property" / "stage2" / "decisions.json")
        .read_text(),
    )
    assert decisions[1]["edit_delta"]["repaired_prior_for_consistency_conflict"][
        "prior_atom"
    ] == broad_floor.name


def test_explicit_prior_repair_failure_does_not_repair_current_property(
    tmp_path: Path,
    workspace: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec_path, schema_path = workspace
    prior_ceiling = PropertyAtom(
        name="owner_only_admin_ceiling",
        rationale="too strict owner ceiling",
        plain_english_summary="Owners can read only when admin.",
        source_excerpt="Owners can read their own resources.",
        constraint_type="ceiling",
        action="read",
        principal_types=["User"],
        resource_types=["Resource"],
        reference_cedar=(
            'permit (principal is User, action == Action::"read", resource is Resource)\n'
            "when { principal == resource.owner && principal.isAdmin };\n"
        ),
    )
    valid_floor = PropertyAtom(
        name="owner_read_floor",
        rationale="valid owner floor",
        plain_english_summary="Owners can read.",
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
    current_repair = replace(
        valid_floor,
        name="bad_current_repair",
        reference_cedar=prior_ceiling.reference_cedar,
    )
    repair_calls: list[str] = []

    def fake_symbolic_verify(
        atom: PropertyAtom,
        schema_path_arg: str,
        prior_atoms: list[PropertyAtom] | None = None,
    ) -> None:
        _ = schema_path_arg
        atom.symbolic_verified = True
        atom.symbolic_verification_log = [f"checked {atom.name}"]
        if atom.name == valid_floor.name and prior_atoms:
            atom.symbolic_verified = False
            atom.symbolic_verification_log = [
                "Consistency check failed against `owner_only_admin_ceiling`: "
                "floor owner_read_floor not contained in ceiling owner_only_admin_ceiling",
            ]

    def reviewer(atom: object) -> AtomDecision:
        name = getattr(atom, "name", "?")
        if name == valid_floor.name:
            return AtomDecision(
                atom_name=name,
                action="reject",
                reason=(
                    "approved prior ceiling too broad; repair prior ceiling "
                    "owner_only_admin_ceiling"
                ),
            )
        return _approve(atom)

    def repair_property_atom(
        spec_text: str,
        schema_path_arg: str,
        rejected_atom: PropertyAtom,
        reason: str,
        prior_atoms: list[PropertyAtom],
    ) -> PropertyAtom | None:
        _ = spec_text, schema_path_arg, reason, prior_atoms
        repair_calls.append(rejected_atom.name)
        if rejected_atom.name == prior_ceiling.name:
            return None
        return current_repair

    def repair_planner(*args, **kwargs) -> PropertyRepairPlan:
        _ = args, kwargs
        return PropertyRepairPlan(
            action="repair_prior_property",
            target_atom=prior_ceiling.name,
            reason="repair prior ceiling",
            repair_instruction="repair the approved prior ceiling",
        )

    synth_calls: list[Path] = []

    def synthesize(scenario_dir: Path) -> Path:
        synth_calls.append(scenario_dir)
        return _synthesize_stub(scenario_dir)

    monkeypatch.setattr("autocedar.pipeline.symbolic_verify_atom", fake_symbolic_verify)
    monkeypatch.setattr(
        "autocedar.pipeline.symbolic_consistency_check",
        lambda *args, **kwargs: SimpleNamespace(
            unsat=False,
            core=[],
            detail="",
            tool_error=False,
        ),
    )

    result = author(
        spec_path=spec_path,
        output_dir=tmp_path / "out",
        session_id="prior-repair-fails-no-current-fallback",
        propose_property_atom=_QueuedPropertyProposer(prior_ceiling, valid_floor),
        plan_property_repair=repair_planner,
        repair_property_atom=repair_property_atom,
        review_atom=reviewer,
        synthesize=synthesize,
        schema_path_override=str(schema_path),
    )

    assert repair_calls == [prior_ceiling.name]
    assert [atom.name for atom in result.plan.properties] == [prior_ceiling.name]
    assert result.final_user_approved is False
    assert len(synth_calls) == 1
    assert "stage2/incremental" in str(synth_calls[0])
    assert not (
        tmp_path
        / "out"
        / "prior-repair-fails-no-current-fallback"
        / "stage3"
        / "final_candidate.cedar"
    ).exists()
    decisions = json.loads(
        (
            tmp_path
            / "out"
            / "prior-repair-fails-no-current-fallback"
            / "stage2"
            / "decisions.json"
        ).read_text(),
    )
    assert decisions[-1]["atom_name"] == valid_floor.name
    assert decisions[-1]["action"] == "reject"
    assert decisions[-1]["edit_delta"]["reject_history"][-1]["action"] == (
        "prior_property_repair_failed"
    )


def test_explicit_schema_gap_repair_budget_stops_before_synthesis(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec_path = tmp_path / "policy_spec.md"
    spec_path.write_text("Students can register for current and upcoming offerings.")

    student = EntityAtom(
        name="Student",
        rationale="student principal",
        plain_english_summary="A student.",
        source_excerpt="Students",
    )
    offering = EntityAtom(
        name="CourseOffering",
        rationale="course offering resource",
        plain_english_summary="A course offering.",
        source_excerpt="course offerings",
    )
    register = ActionAtom(
        name="register",
        rationale="registration action",
        plain_english_summary="Register.",
        source_excerpt="register",
        principal_types=["Student"],
        resource_types=["CourseOffering"],
    )
    current_attr = AttributeAtom(
        name="course_offering_is_current",
        rationale="current marker",
        plain_english_summary="Current marker.",
        source_excerpt="current",
        on_entity="CourseOffering",
        field_name="isCurrent",
        cedar_type="Bool",
    )
    weak_current = PropertyAtom(
        name="weak_current",
        rationale="first gap",
        plain_english_summary="Weak current property.",
        source_excerpt="current offerings",
        constraint_type="floor",
        action="register",
        principal_types=["Student"],
        resource_types=["CourseOffering"],
        reference_cedar='permit (principal, action == Action::"register", resource);',
    )
    approved_after_first_repair = replace(
        weak_current,
        name="current_ok",
        reference_cedar='permit (principal, action == Action::"register", resource) when { resource.isCurrent };',
    )
    weak_upcoming = replace(weak_current, name="weak_upcoming", source_excerpt="upcoming offerings")
    properties = [weak_current, approved_after_first_repair, weak_upcoming]
    schema_calls = 0

    def schema_proposer(text: str) -> list[object]:
        nonlocal schema_calls
        schema_calls += 1
        if schema_calls == 1:
            return [student, offering, register]
        return [current_attr]

    def property_proposer(
        text: str,
        schema_path_arg: str,
        prior_atoms: list[PropertyAtom],
        prior_decisions: list[AtomDecision],
    ) -> PropertyAtom | None:
        _ = text, schema_path_arg, prior_atoms, prior_decisions
        if not properties:
            return None
        return properties.pop(0)

    def reviewer(atom: object) -> AtomDecision:
        if not isinstance(atom, PropertyAtom):
            return _approve(atom)
        if atom.name == "weak_current":
            return AtomDecision(atom_name=atom.name, action="reject", reason="schema needs current marker")
        if atom.name == "weak_upcoming":
            return AtomDecision(atom_name=atom.name, action="reject", reason="schema needs upcoming marker")
        return _approve(atom)

    def fake_compose_and_validate(draft, schema_path_arg, llm=None, spec_text="", max_attempts=3):
        from autocedar.schema_atomizer import FixAttempt, compose_schema

        _ = llm, spec_text, max_attempts
        schema_text = compose_schema(draft)
        schema_path_arg.write_text(schema_text)
        return SimpleNamespace(
            schema_text=schema_text,
            schema_path=schema_path_arg,
            succeeded=True,
            attempts=[FixAttempt(attempt_number=1, schema_text=schema_text, validator_passed=True)],
        )

    def fail_synthesize(scenario_dir: Path) -> Path:
        _ = scenario_dir
        raise AssertionError("schema repair budget stop must happen before Stage 3")

    monkeypatch.setattr("autocedar.pipeline.compose_and_validate", fake_compose_and_validate)
    monkeypatch.setattr(
        "autocedar.pipeline.symbolic_verify_atom",
        lambda atom, schema_path_arg, prior_atoms=None: setattr(atom, "symbolic_verified", True),
    )

    result = author(
        spec_path=spec_path,
        output_dir=tmp_path / "out",
        session_id="schema-budget",
        propose_schema_atoms=schema_proposer,
        propose_property_atom=property_proposer,
        plan_property_repair=lambda *args, **kwargs: _repair_schema_plan(
            "add the missing lifecycle marker to the schema",
        ),
        review_atom=reviewer,
        synthesize=fail_synthesize,
        max_schema_gap_repairs=1,
    )

    assert result.final_user_approved is False
    assert "repair budget" in result.notes[0]
    assert not (tmp_path / "out" / "schema-budget" / "stage3" / "final_candidate.cedar").exists()


def test_hitl_schema_gap_rejection_stops_when_repair_is_unavailable(
    tmp_path: Path,
    workspace: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec_path, schema_path = workspace

    def fake_symbolic_verify(
        atom: PropertyAtom,
        schema_path_arg: str,
        prior_atoms: list[PropertyAtom] | None = None,
    ) -> None:
        _ = schema_path_arg, prior_atoms
        atom.symbolic_verified = True
        atom.symbolic_verification_log = [f"checked {atom.name}"]

    def reviewer(atom: object) -> AtomDecision:
        return AtomDecision(
            atom_name=getattr(atom, "name", "?"),
            action="reject",
            reason=(
                "schema needs a current/previous/upcoming marker before this "
                "property is acceptable"
            ),
        )

    def fail_consistency(*args: object, **kwargs: object) -> object:
        raise AssertionError("schema-gap HITL rejection must stop before consistency checks")

    def fail_synthesize(scenario_dir: Path) -> Path:
        _ = scenario_dir
        raise AssertionError("schema-gap HITL rejection must stop before Stage 3")

    monkeypatch.setattr("autocedar.pipeline.symbolic_verify_atom", fake_symbolic_verify)
    monkeypatch.setattr("autocedar.pipeline.symbolic_consistency_check", fail_consistency)

    result = author(
        spec_path=spec_path,
        output_dir=tmp_path / "out",
        session_id="schema-gap-stop",
        propose_property_atom=_QueuedPropertyProposer(_owner_only_ceiling()),
        plan_property_repair=lambda *args, **kwargs: _repair_schema_plan(
            "add current/previous/upcoming lifecycle markers to the schema",
        ),
        review_atom=reviewer,
        synthesize=fail_synthesize,
        schema_path_override=str(schema_path),
    )

    assert result.final_user_approved is False
    assert result.candidate_path == Path("")
    assert "could not produce an approved schema repair" in result.notes[0]

    session_dir = tmp_path / "out" / "schema-gap-stop"
    gaps = json.loads((session_dir / "stage1_5" / "schema_gaps.json").read_text())
    assert gaps == [
        {
            "atom_name": "owner_only_read",
            "stage": "stage2_property_review",
            "reason": "add current/previous/upcoming lifecycle markers to the schema",
            "tags": [],
            "required_action": "repair_schema_before_synthesis",
            "repair_plan": {
                "action": "repair_schema",
                "reason": "add current/previous/upcoming lifecycle markers to the schema",
                "repair_instruction": (
                    "add current/previous/upcoming lifecycle markers to the schema"
                ),
            },
        },
    ]
    assert not (session_dir / "stage1_75" / "unsat_core.json").exists()
    assert not (session_dir / "stage2" / "final_plan" / "verification_plan.py").exists()
    assert not (session_dir / "stage3" / "final_candidate.cedar").exists()


def test_property_required_schema_support_triggers_repair_before_review(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    spec_path = tmp_path / "policy_spec.md"
    spec_path.write_text("Administrators can read credentials.")
    schema_path = tmp_path / "schema.cedarschema"
    schema_path.write_text(textwrap.dedent("""\
        entity User;
        entity Admin;
        entity Document;
        entity Credential;

        action read appliesTo {
            principal: [User],
            resource: [Document],
        };
    """))

    monkeypatch.setattr("autocedar.pipeline.cedar_validate_schema", lambda path: (True, ""))
    monkeypatch.setattr(
        "autocedar.pipeline.symbolic_consistency_check",
        lambda plan, schema: SimpleNamespace(
            unsat=False,
            core=[],
            detail="",
            tool_error=False,
        ),
    )

    def fail_if_property_verifier_runs(*args: object, **kwargs: object) -> None:
        _ = args, kwargs
        raise AssertionError("property verification should wait for schema repair")

    monkeypatch.setattr("autocedar.pipeline.symbolic_verify_atom", fail_if_property_verifier_runs)

    proposed = _admin_credential_read_floor_with_missing_action_support()
    proposer_calls = 0

    def property_proposer(
        spec_text: str,
        schema_path_arg: str,
        prior_atoms: list[PropertyAtom],
        prior_decisions: list[AtomDecision],
    ) -> PropertyAtom | None:
        nonlocal proposer_calls
        _ = spec_text, prior_atoms, prior_decisions
        proposer_calls += 1
        if proposer_calls == 1:
            assert "principal: [User]" in Path(schema_path_arg).read_text()
            return proposed
        assert "principal: [User, Admin]" in Path(schema_path_arg).read_text()
        assert "resource: [Document, Credential]" in Path(schema_path_arg).read_text()
        return None

    repair_specs: list[str] = []

    def schema_proposer(spec_text: str) -> list[ActionAtom]:
        repair_specs.append(spec_text)
        return [
            ActionAtom(
                name="read",
                rationale="add missing action support",
                plain_english_summary="Allow admins to read credentials.",
                source_excerpt="Administrators can read credentials.",
                principal_types=["Admin"],
                resource_types=["Credential"],
            ),
        ]

    reviewed: list[object] = []

    def reviewer(atom: object) -> AtomDecision:
        reviewed.append(atom)
        return _approve(atom)

    result = author(
        spec_path=spec_path,
        output_dir=tmp_path / "out",
        session_id="schema-support",
        propose_schema_atoms=schema_proposer,
        propose_property_atom=property_proposer,
        review_atom=reviewer,
        synthesize=_synthesize_stub,
        schema_path_override=str(schema_path),
    )

    assert result.final_user_approved is True
    assert proposer_calls == 2
    assert repair_specs
    assert "action `read` does not include principal type `Admin`" in repair_specs[0]
    assert "action `read` does not include resource type `Credential`" in repair_specs[0]
    assert [type(atom) for atom in reviewed] == [ActionAtom]
    assert "principal: [User, Admin]" in result.schema_text
    assert "resource: [Document, Credential]" in result.schema_text
    gaps = json.loads(
        (tmp_path / "out" / "schema-support" / "stage1_5" / "schema_gaps.json").read_text(),
    )
    assert gaps[0]["stage"] == "stage2_pre_review_schema_support"


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

    property_proposer = _QueuedPropertyProposer(_owner_only_ceiling())

    author(
        spec_path=spec_path,
        output_dir=output_dir,
        session_id="t2",
        propose_property_atom=property_proposer,
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
    # The injected reviewer models an explicit interactive approval;
    # symbolic_verified independently mirrors the actual symcc result.
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

    property_proposer = _QueuedPropertyProposer(_owner_only_ceiling(), _owner_must_floor())

    author(
        spec_path=spec_path,
        output_dir=output_dir,
        session_id="t3",
        propose_property_atom=property_proposer,
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

    property_proposer = _QueuedPropertyProposer(_owner_only_ceiling())

    author(
        spec_path=spec_path,
        output_dir=output_dir,
        session_id="t4",
        propose_property_atom=property_proposer,
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

    property_proposer = _QueuedPropertyProposer(_owner_only_ceiling(), bad_floor)

    result = author(
        spec_path=spec_path,
        output_dir=output_dir,
        session_id="t5",
        propose_property_atom=property_proposer,
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
