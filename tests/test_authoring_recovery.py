"""Fault-injection tests for persistence/control flow, not semantic HITL approval."""

import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from autocedar import pipeline
from autocedar.atoms import EntityAtom, to_dict
from autocedar.corpus import AtomDecision, Session
from autocedar.persistence import atomic_write_text, find_resumable_session, write_json
from autocedar.ui.terminal import ReviewedAtom, auto_approve
from tests.test_pipeline import MINIMAL_SCHEMA, _owner_must_floor, _owner_only_ceiling


@pytest.fixture
def plumbing(monkeypatch, tmp_path):
    spec = tmp_path / "spec.md"
    spec.write_text("Owners can read their own resources.")
    schema = tmp_path / "schema.cedarschema"
    schema.write_text(MINIMAL_SCHEMA)
    monkeypatch.setattr(pipeline, "cedar_validate_schema", lambda *_: (True, ""))

    def verify(atom, *_args, **_kwargs):
        atom.symbolic_verified = True
        atom.symbolic_verification_log = ["test fixture only"]

    monkeypatch.setattr(pipeline, "symbolic_verify_atom", verify)
    monkeypatch.setattr(pipeline, "symbolic_consistency_check", lambda *_: SimpleNamespace(
        unsat=False, core=[], detail="", tool_error=False))
    monkeypatch.setattr(pipeline, "generate_atom_traceback", lambda *_: [])
    calls = []

    def synthesize(directory):
        calls.append(directory)
        path = directory / "candidate.cedar"
        path.write_text("permit(principal, action, resource);")
        return path

    return dict(spec_path=spec, output_dir=tmp_path / "runs", schema_path_override=str(schema),
                synthesize=synthesize), calls


def test_resume_keeps_approval_and_unreviewed_bundle_without_new_proposal(plumbing):
    kwargs, synth_calls = plumbing
    original = kwargs["output_dir"] / "original"
    reviewed = []

    def interrupted_review(atom):
        reviewed.append(atom.name)
        if len(reviewed) == 2:
            raise TimeoutError("simulated process interruption")
        return auto_approve(atom)

    with pytest.raises(TimeoutError):
        pipeline.author(**kwargs, session_id="original", review_atom=interrupted_review,
                        propose_property_atom=lambda *_: [_owner_must_floor(), _owner_only_ceiling()])
    assert synth_calls == []
    snapshot = json.loads((original / "stage2" / "checkpoint.json").read_text())
    assert len(snapshot["approved_atoms"]) == 1
    assert len(snapshot["decisions"]) == 1
    assert len(snapshot["pending_properties"]) == 1
    before = {str(p.relative_to(original)): p.read_bytes() for p in original.rglob("*") if p.is_file()}
    resumed_reviews = []

    def resume_review(atom):
        resumed_reviews.append(atom.name)
        return auto_approve(atom)

    def no_new_proposals(*_):
        pytest.fail("The queued proposal must survive an interruption")

    result = pipeline.author(**kwargs, session_id="resumed", resume_from=original,
                             review_atom=resume_review, propose_property_atom=no_new_proposals)
    assert resumed_reviews == ["owner_only_read"]
    assert len(result.plan.properties) == 2
    assert len(synth_calls) == 1
    assert result.final_user_approved is False  # Scripted plumbing does not establish intent.
    assert before == {str(p.relative_to(original)): p.read_bytes() for p in original.rglob("*") if p.is_file()}


def test_resume_rejects_changed_requirements_before_creating_output(plumbing):
    kwargs, _ = plumbing
    source = Session("original", kwargs["output_dir"])
    source.write_input_spec("A different requirement.")
    with pytest.raises(ValueError, match="differs"):
        pipeline.author(**kwargs, session_id="changed", resume_from=source.base)
    assert not (kwargs["output_dir"] / "changed").exists()


def test_session_id_collision_never_overwrites_existing_work(tmp_path):
    source = Session("same", tmp_path)
    source.write_input_spec("keep this")
    with pytest.raises(FileExistsError, match="already exists"):
        Session("same", tmp_path)
    assert (source.base / "input" / "policy_spec.md").read_text() == "keep this"


def test_atomic_write_failure_leaves_previous_checkpoint(monkeypatch, tmp_path):
    path = tmp_path / "checkpoint.json"
    atomic_write_text(path, "previous state")

    def fail_replace(*_):
        raise OSError("simulated disk failure")

    monkeypatch.setattr("autocedar.persistence.os.replace", fail_replace)
    with pytest.raises(OSError):
        atomic_write_text(path, "new state")
    assert path.read_text() == "previous state"
    assert list(tmp_path.iterdir()) == [path]


def test_legacy_resume_preserves_independent_ceilings_and_verifier_status(plumbing):
    kwargs, _ = plumbing
    source = Session("legacy", kwargs["output_dir"])
    source.write_input_spec(kwargs["spec_path"].read_text())
    source.write_stage1_final_schema(MINIMAL_SCHEMA)
    older = replace(_owner_only_ceiling(), source_excerpt="[source_id: src.root.p0001.l1]", symbolic_verified=False)
    newer = replace(older, name="independent_safety", source_excerpt="[source_id: src.root.p0001.l1] [source_id: src.root.p0002.l2]",
                    reference_cedar=older.reference_cedar.replace("principal == resource.owner", "principal.isAdmin"))
    source.write_stage2_proposed_atoms([older, newer])
    source.write_stage2_approved_atoms([older, newer])
    source.write_stage2_decisions([auto_approve(a) for a in [older, newer]])
    restored = pipeline._load_resume_checkpoint(source.base)
    assert [to_dict(a) for a in restored.approved_property_atoms] == [to_dict(older), to_dict(newer)]
    assert restored.schema_text == MINIMAL_SCHEMA


def test_stage1_resume_preserves_edited_atom_and_pending_schema_queue(plumbing, monkeypatch):
    kwargs, _ = plumbing
    kwargs = dict(kwargs)
    kwargs.pop("schema_path_override")
    original = kwargs["output_dir"] / "schema-interrupted"
    atoms = [EntityAtom(name=name, rationale="fixture", plain_english_summary=name,
                        source_excerpt="Owners can read their own resources.") for name in ["User", "Resource"]]
    seen = []

    def review(atom):
        seen.append(atom.name)
        if len(seen) == 2:
            raise TimeoutError("schema interrupted")
        edited = replace(atom, plain_english_summary="An edited summary")
        return ReviewedAtom(atom=edited, decision=auto_approve(edited))

    with pytest.raises(TimeoutError):
        pipeline.author(**kwargs, session_id="schema-interrupted", review_atom=review,
                        propose_schema_atoms=lambda *_: atoms, propose_property_atom=lambda *_: [])

    def compose(draft, path, **_):
        assert draft.entities["User"].plain_english_summary == "An edited summary"
        path.write_text(MINIMAL_SCHEMA)
        return SimpleNamespace(schema_text=MINIMAL_SCHEMA, attempts=[], succeeded=True)

    monkeypatch.setattr(pipeline, "compose_and_validate", compose)
    resumed = []

    def no_proposal(*_):
        pytest.fail("Do not regenerate the schema bundle")

    pipeline.author(**kwargs, session_id="schema-resumed", resume_from=original,
                    review_atom=lambda a: resumed.append(a.name) or auto_approve(a),
                    propose_schema_atoms=no_proposal, propose_property_atom=lambda *_: [])
    assert resumed == ["Resource"]


def test_completed_sources_not_requeried_after_timeout(plumbing):
    kwargs, _ = plumbing
    kwargs["spec_path"].write_text("Users can read.\n\nUsers can write.")
    calls = []

    def propose(packet, *_):
        calls.append(packet)
        if len(calls) == 2:
            raise TimeoutError("next source timed out")
        return []

    with pytest.raises(TimeoutError):
        pipeline.author(**kwargs, session_id="timeout", review_atom=auto_approve, propose_property_atom=propose)
    source = kwargs["output_dir"] / "timeout"
    checkpoint = pipeline._load_resume_checkpoint(source)
    assert len(checkpoint.completed_property_node_ids) == 1
    assert find_resumable_session(kwargs["output_dir"], kwargs["spec_path"].read_text()) == source
    resumed_calls = []
    pipeline.author(**kwargs, session_id="resume", resume_from=source, review_atom=auto_approve,
                    propose_property_atom=lambda packet, *_: resumed_calls.append(packet) or [])
    assert len(resumed_calls) == 1


def test_repeated_identical_no_progress_stops_before_global_budget(plumbing):
    kwargs, _ = plumbing
    calls = []

    def propose(*_):
        calls.append(1)
        return [_owner_must_floor()]  # Missing safety boundary blocks completion.

    with pytest.raises(RuntimeError, match="no progress"):
        pipeline.author(**kwargs, session_id="stalled", review_atom=auto_approve, propose_property_atom=propose)
    assert len(calls) == 4  # First approval changes state, then three identical proposals.


def test_schema_gap_repair_saves_each_review_before_next_prompt(plumbing, monkeypatch):
    kwargs, _ = plumbing
    session = Session("gap", kwargs["output_dir"])
    records, approved, names = [], [], set()
    atoms = [EntityAtom(name=n, rationale="fixture", plain_english_summary=n,
                        source_excerpt="A source requirement.") for n in ["ExtraA", "ExtraB"]]
    seen = []

    def interrupted(atom):
        seen.append(atom.name)
        if len(seen) == 2:
            raise TimeoutError("gap review interrupted")
        return auto_approve(atom)

    common = dict(spec_text="A source requirement.", schema_text=MINIMAL_SCHEMA,
                  schema_path=Path(kwargs["schema_path_override"]), gap={"atom_name": "needs_support", "reason": "Missing entities"},
                  session=session, fix_schema=None, draft=None, approved_schema_atoms=approved,
                  approved_schema_names=names, repair_records=records)
    with pytest.raises(TimeoutError):
        pipeline._repair_schema_gap_and_validate(**common, review_atom=interrupted,
                                                 propose_schema_atoms=lambda *_: atoms)
    persisted = json.loads((session.base / "stage1_5" / "schema_gap_repairs.json").read_text())
    assert len(persisted[0]["approved_atoms"]) == 1
    monkeypatch.setattr(pipeline, "apply_schema_atoms_to_text", lambda text, _atoms: text)
    reviewed = []
    common["repair_records"] = persisted
    result = pipeline._repair_schema_gap_and_validate(
        **common, review_atom=lambda a: reviewed.append(a.name) or auto_approve(a),
        propose_schema_atoms=lambda *_: pytest.fail("Saved schema repair queue must be reused"))
    assert result == MINIMAL_SCHEMA
    assert reviewed == ["ExtraB"]
