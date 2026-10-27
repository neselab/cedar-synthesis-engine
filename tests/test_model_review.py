"""Tests for ``autocedar.model_review`` and the ``--model-review`` CLI wiring."""

from __future__ import annotations

import argparse
from pathlib import Path
from types import SimpleNamespace

import pytest

import autocedar.cli as cli
from autocedar.atoms import EntityAtom, PropertyAtom
from autocedar.llm import AtomReviewResponse
from autocedar.model_review import ModelReviewer


def _property(name: str = "release_requires_inspector", *, verified: bool = True) -> PropertyAtom:
    return PropertyAtom(
        name=name,
        rationale="bound",
        plain_english_summary="Only the recorded inspector may release the work order.",
        source_excerpt="Access requires that the user equals the work order's inspector.",
        constraint_type="ceiling",
        action="releaseToProduction",
        principal_types=["User"],
        resource_types=["WorkOrder"],
        reference_cedar=(
            'permit (principal is User, action == Action::"releaseToProduction", '
            "resource is WorkOrder) when { principal == resource.inspector };"
        ),
        symbolic_verified=verified,
        symbolic_verification_log=[] if verified else ["type-correct: FAILED (rc=3)"],
    )


class FakeLLM:
    def __init__(self, *decisions: tuple[str, str]) -> None:
        self.decisions = list(decisions)
        self.calls: list[dict] = []

    def review_atom_against_requirements(self, **kwargs):
        self.calls.append(kwargs)
        decision, reason = self.decisions.pop(0)
        return AtomReviewResponse(decision=decision, reason=reason)


def test_failed_checks_are_rejected_without_asking_the_model() -> None:
    llm = FakeLLM()
    decision = ModelReviewer(llm, "spec")(_property(verified=False))

    assert decision.action == "reject"
    assert "Symbolic verification failed" in decision.reason
    assert "type-correct: FAILED" in decision.reason
    assert llm.calls == []


def test_model_decisions_are_recorded_as_model_review_not_human_approval() -> None:
    llm = FakeLLM(
        ("approve", "Matches the release section."),
        ("reject", "This requirement belongs to releaseToProduction, not signoffWorkOrder."),
    )
    reviewer = ModelReviewer(llm, "# Requirements")
    reviewer.schema_ready("entity User;")
    first = _property()

    approved = reviewer(first)
    rejected = reviewer(_property("signoff_requires_inspector"))

    assert approved.action == "approve"
    assert approved.intent_acknowledged_by_user is False
    assert approved.edit_delta == {"review_channel": "model", "model_review": "Matches the release section."}
    assert rejected.action == "reject"
    assert rejected.reason == (
        "Model review: This requirement belongs to releaseToProduction, not signoffWorkOrder."
    )
    assert rejected.intent_acknowledged_by_user is False
    assert llm.calls[0]["spec_text"] == "# Requirements"
    assert llm.calls[0]["schema_text"] == "entity User;"
    # Earlier approvals are shown to the model as context.
    assert llm.calls[1]["approved_atoms"] == [first]


def test_schema_atoms_are_reviewed_by_the_model() -> None:
    llm = FakeLLM(("reject", "disputeCategory is compared by membership, so it is a set."))
    atom = EntityAtom(name="Folio", rationale="r", plain_english_summary="s", source_excerpt="e")

    decision = ModelReviewer(llm, "spec")(atom)

    assert decision.action == "reject"
    assert llm.calls[0]["atom"] is atom


@pytest.mark.parametrize("flag", ["--model-review", "--auto-approve"])
def test_both_flag_names_turn_on_model_review(flag: str) -> None:
    args = cli._build_parser().parse_args(["author", flag, "spec.md", "--out", "out"])

    assert cli._model_review_enabled(args)
    assert args.spec == "spec.md"


def test_author_routes_atoms_through_the_model_reviewer(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    spec = tmp_path / "spec.md"
    spec.write_text("Only the recorded inspector may release a work order.")
    llm = FakeLLM(("reject", "Wrong action."))
    monkeypatch.setattr(cli, "LLMClient", lambda **kwargs: llm)
    monkeypatch.setattr(cli, "make_harness_synthesizer", lambda **kwargs: object())
    decisions = []

    def fake_author_pipeline(**kwargs):
        decisions.append(kwargs["review_atom"](_property()))
        return SimpleNamespace(
            session_dir=tmp_path, candidate_path=Path(""), final_user_approved=False, notes=[],
        )

    monkeypatch.setattr(cli, "author_pipeline", fake_author_pipeline)
    cli._cmd_author(argparse.Namespace(
        spec=str(spec), out=str(tmp_path / "out"), session_id=None, schema=None,
        model="m", effort="low", model_review=True,
    ))

    assert decisions[0].action == "reject"
    assert decisions[0].reason == "Model review: Wrong action."
    assert llm.calls[0]["spec_text"] == spec.read_text()


def test_llm_review_call_returns_the_parsed_decision(monkeypatch: pytest.MonkeyPatch) -> None:
    from autocedar.llm import LLMClient

    client = LLMClient.__new__(LLMClient)
    client._provider = "codex"
    client._effort = "low"
    seen = {}

    def fake_call_parse(**kwargs):
        seen.update(kwargs)
        return SimpleNamespace(parsed_output=AtomReviewResponse(decision="reject", reason="Wrong action."))

    monkeypatch.setattr(client, "_call_parse", fake_call_parse)

    review = client.review_atom_against_requirements(
        atom=_property(), spec_text="spec", schema_text="entity User;", approved_atoms=[],
    )

    assert review == AtomReviewResponse(decision="reject", reason="Wrong action.")
    assert seen["output_format"] is AtomReviewResponse
    assert "release_requires_inspector" in seen["user_turn"]


def test_model_reviewer_reviews_the_intent_map_with_its_outline() -> None:
    from autocedar.intent_map import IntentMap

    class MapLLM:
        def __init__(self) -> None:
            self.seen = {}

        def review_intent_map(self, **kwargs):
            self.seen = kwargs
            return AtomReviewResponse(decision="reject", reason="p0037 belongs to release.")

    llm = MapLLM()
    m = IntentMap(review_text="INTENT MAP ...", outline='<node id="p1">...</node>')

    decision = ModelReviewer(llm, "raw spec")(m)

    assert decision.action == "reject"
    assert decision.atom_name == "intent_map"
    assert decision.intent_acknowledged_by_user is False
    assert llm.seen["outline"] == '<node id="p1">...</node>'


def test_model_reviewer_answers_whether_the_permission_list_is_complete() -> None:
    from autocedar.intent_map import MapScope, PermissionsQuestion

    class QuestionLLM:
        def __init__(self) -> None:
            self.seen = {}

        def answer_permissions_question(self, **kwargs):
            self.seen = kwargs
            return AtomReviewResponse(decision="approve", reason="The numbered list reads as the full grant list.")

    llm = QuestionLLM()
    question = PermissionsQuestion(
        scopes=[MapScope("s_release", "release", "User", "WorkOrder", None)],
        outline="<spec outline>",
    )

    decision = ModelReviewer(llm, "raw spec")(question)

    assert decision.action == "approve"
    assert decision.atom_name == "permissions_complete"
    assert decision.intent_acknowledged_by_user is False
    assert decision.edit_delta["review_channel"] == "model"
    assert llm.seen["question"] is question
    assert llm.seen["outline"] == "<spec outline>"


def test_model_map_review_passes_its_named_objections_on() -> None:
    from autocedar.intent_map import IntentMap
    from autocedar.llm import MapReviewResponse

    class MapLLM:
        def review_intent_map(self, **kwargs):
            return MapReviewResponse.model_validate({
                "decision": "reject",
                "reason": "One condition is under the wrong action.",
                "objections": [{"kind": "move_condition", "node_id": "p4", "slice_ids": ["s2"],
                                "detail": "p4 is in the sign-off section."}],
            })

    decision = ModelReviewer(MapLLM(), "spec")(IntentMap(review_text="INTENT MAP"))

    assert decision.action == "reject"
    assert decision.edit_delta["map_objections"][0]["node_id"] == "p4"
    assert decision.edit_delta["map_objections"][0]["slice_ids"] == ["s2"]
