"""Tests for ``autocedar.ui.terminal`` — interactive review loop.

Covers acceptance criterion 4 of ``docs/HITL_STEP_C_PLAN.md`` §3: all
six keys (A/R/E/Q/S/V) dispatch correctly, the AtomDecision captures
both ``intent_acknowledged_by_user`` and ``symbolic_verified``, and
scripted ``input_fn`` walks through each path without touching stdin.
"""

from __future__ import annotations

from typing import Any, Iterable

import pytest

from autocedar.atoms import (
    ActionAtom,
    AttributeAtom,
    EntityAtom,
    PropertyAtom,
    TypeAliasAtom,
)
from autocedar.ui.terminal import (
    VERIFIED_BADGE,
    format_symbolic_verification_log,
    interactive_review_loop,
    render_property_atom,
    render_property_reference,
    render_schema_atom,
    render_schema_declaration,
)


# ---------------------------------------------------------------------------
# Fake I/O.
# ---------------------------------------------------------------------------


class _ScriptedInput:
    """Iterator-backed ``input_fn`` stand-in for tests."""

    def __init__(self, lines: Iterable[str]) -> None:
        self._iter = iter(list(lines))

    def __call__(self, prompt: str = "") -> str:
        try:
            return next(self._iter)
        except StopIteration as e:
            raise AssertionError(
                f"ran out of scripted input at prompt {prompt!r}",
            ) from e


class _CaptureOutput:
    """Captures ``output_fn`` calls for assertions."""

    def __init__(self) -> None:
        self.lines: list[str] = []

    def __call__(self, line: str) -> None:
        self.lines.append(line)

    @property
    def text(self) -> str:
        return "\n".join(self.lines)


# ---------------------------------------------------------------------------
# Atom fixtures.
# ---------------------------------------------------------------------------


def _entity() -> EntityAtom:
    return EntityAtom(
        name="User",
        rationale="principal",
        plain_english_summary="The principal in every request.",
        source_excerpt="Doctors and nurses on the patient's care team can read.",
    )


def _attribute() -> AttributeAtom:
    return AttributeAtom(
        name="User__role",
        rationale="single string role",
        plain_english_summary="Each user has one role.",
        source_excerpt="Doctors and nurses ...",
        on_entity="User",
        field_name="role",
        cedar_type="String",
        alternatives_considered=["Set<String>"],
    )


def _action() -> ActionAtom:
    return ActionAtom(
        name="read",
        rationale="primary read action",
        plain_english_summary="Read a record.",
        source_excerpt="...",
        principal_types=["User"],
        resource_types=["Record"],
    )


def _property() -> PropertyAtom:
    return PropertyAtom(
        name="owner_only_read",
        rationale="bound",
        plain_english_summary="Only the owner reads.",
        source_excerpt="Owners can read their own resources.",
        constraint_type="ceiling",
        action="read",
        principal_types=["User"],
        resource_types=["Record"],
        reference_cedar=(
            'permit (principal is User, action == Action::"read", resource is Record)\n'
            "when { principal == resource.owner };"
        ),
        symbolic_verified=True,
        symbolic_verification_log=[
            "type-correct: ok",
            "satisfiable: ok",
            "sugar-universal: ok (not applicable to primitives)",
        ],
    )


def _liveness_property() -> PropertyAtom:
    return PropertyAtom(
        name="read_liveness",
        rationale="at least one read must be allowed",
        plain_english_summary="At least one read request is permitted.",
        source_excerpt="Users can read public records.",
        constraint_type="liveness",
        action="read",
        principal_types=["User"],
        resource_types=["Record"],
        symbolic_verified=True,
        symbolic_verification_log=[
            "type-correct: ok (n/a)",
            "satisfiable: ok (liveness atom has no reference encoding)",
            "sugar-universal: ok (not applicable to primitives)",
        ],
    )


# ---------------------------------------------------------------------------
# render helpers.
# ---------------------------------------------------------------------------


def test_render_schema_atom_includes_kind_and_summary() -> None:
    text = render_schema_atom(_entity(), 1, 3)
    assert "ENTITY" in text
    assert "User" in text
    assert "The principal in every request." in text
    assert "Source excerpt:" in text
    # Six-key footer.
    assert "[A]pprove" in text
    assert "[V]iew patches" in text


def test_render_schema_declaration_for_each_kind() -> None:
    assert "entity User" in render_schema_declaration(_entity())
    assert "role: String" in render_schema_declaration(_attribute())
    assert "action read appliesTo" in render_schema_declaration(_action())
    assert "type Address" in render_schema_declaration(
        TypeAliasAtom(
            name="Address", rationale="...",
            plain_english_summary="...", source_excerpt="...",
            cedar_type="{ street: String }",
        ),
    )


def test_render_property_atom_uses_verified_badge() -> None:
    text = render_property_atom(_property(), 1, 1)
    assert VERIFIED_BADGE in text
    assert "Satisfiability check: OK" in text
    assert "sugar-universal" not in text


def test_render_property_atom_supports_unknown_total() -> None:
    text = render_property_atom(_property(), 3, None)
    assert "[Property 3]" in text
    assert "of 3" not in text


def test_symbolic_log_formatter_explains_missing_schema_type() -> None:
    lines = format_symbolic_verification_log([
        "type-correct: FAILED (cedar validate rc=1: failed to resolve type: Vitals)",
        "satisfiable: ok",
        "sugar-universal: ok (not applicable to primitives)",
    ])

    rendered = "\n".join(lines)
    assert "approved schema does not define `Vitals`" in rendered
    assert "Satisfiability check: OK" in rendered
    assert "sugar-universal" not in rendered


def test_render_liveness_reference_explains_absent_cedar_body() -> None:
    text = render_property_reference(_liveness_property())
    assert "Liveness property" in text
    assert "no standalone reference policy" in text
    assert "Action: read" in text


# ---------------------------------------------------------------------------
# Interactive loop — happy path (approve all).
# ---------------------------------------------------------------------------


def test_loop_approves_each_atom_with_intent_ack_set() -> None:
    captured = _CaptureOutput()
    scripted = _ScriptedInput(["A", "A", "A"])

    reviewed = interactive_review_loop(
        [_entity(), _attribute(), _action()],
        input_fn=scripted,
        output_fn=captured,
    )

    assert [r.decision.action for r in reviewed] == ["approve", "approve", "approve"]
    # intent_acknowledged_by_user is the §1.4 contract.
    assert all(r.decision.intent_acknowledged_by_user for r in reviewed)
    # The corpus log distinguishes intent from symbolic_verified;
    # Stage 1 atoms haven't been symcc-checked so symbolic_verified
    # stays False (no flag set anywhere in the loop). The pipeline
    # will set it later for Stage 2 atoms.
    assert all(r.decision.symbolic_verified is False for r in reviewed)


# ---------------------------------------------------------------------------
# [E] edit — apply field=value updates.
# ---------------------------------------------------------------------------


def test_edit_key_updates_field_and_re_presents() -> None:
    captured = _CaptureOutput()
    scripted = _ScriptedInput([
        "E",                                      # press edit
        "plain_english_summary=A simpler summary",
        "A",                                      # then approve
    ])
    reviewed = interactive_review_loop(
        [_entity()],
        input_fn=scripted,
        output_fn=captured,
    )
    assert reviewed[0].atom.plain_english_summary == "A simpler summary"
    assert reviewed[0].decision.action == "approve"
    # Edit log captured in edit_delta for the corpus.
    edits = reviewed[0].decision.edit_delta.get("edits", [])
    assert len(edits) == 1
    assert edits[0]["field"] == "plain_english_summary"


def test_edit_rejects_unknown_field_and_leaves_atom_unchanged() -> None:
    captured = _CaptureOutput()
    scripted = _ScriptedInput([
        "E",
        "garbage=42",   # field doesn't exist on EntityAtom
        "A",
    ])
    reviewed = interactive_review_loop(
        [_entity()],
        input_fn=scripted,
        output_fn=captured,
    )
    assert reviewed[0].atom.name == "User"
    assert "edit rejected" in captured.text


def test_edit_attribute_optional_flag_parses_bool() -> None:
    captured = _CaptureOutput()
    scripted = _ScriptedInput(["E", "optional=true", "A"])
    reviewed = interactive_review_loop(
        [_attribute()],
        input_fn=scripted,
        output_fn=captured,
    )
    attr = reviewed[0].atom
    assert isinstance(attr, AttributeAtom)
    assert attr.optional is True


def test_edit_action_principal_types_parses_csv() -> None:
    captured = _CaptureOutput()
    scripted = _ScriptedInput([
        "E",
        "principal_types=User, ApiKey, Bot",
        "A",
    ])
    reviewed = interactive_review_loop(
        [_action()],
        input_fn=scripted,
        output_fn=captured,
    )
    action = reviewed[0].atom
    assert isinstance(action, ActionAtom)
    assert action.principal_types == ["User", "ApiKey", "Bot"]


def test_property_atom_approval_preserves_symbolic_verified() -> None:
    captured = _CaptureOutput()
    scripted = _ScriptedInput(["A"])

    reviewed = interactive_review_loop(
        [_property()],
        input_fn=scripted,
        output_fn=captured,
    )

    assert reviewed[0].decision.action == "approve"
    assert reviewed[0].decision.symbolic_verified is True
    assert "Property 1 of 1" in captured.text


def test_edit_property_action_field() -> None:
    captured = _CaptureOutput()
    scripted = _ScriptedInput(["E", "action=view", "A"])

    reviewed = interactive_review_loop(
        [_property()],
        input_fn=scripted,
        output_fn=captured,
    )

    atom = reviewed[0].atom
    assert isinstance(atom, PropertyAtom)
    assert atom.action == "view"


# ---------------------------------------------------------------------------
# [S] see Cedar — prints declaration, stays on atom.
# ---------------------------------------------------------------------------


def test_see_cedar_key_prints_declaration_then_loops() -> None:
    captured = _CaptureOutput()
    scripted = _ScriptedInput(["S", "A"])
    reviewed = interactive_review_loop(
        [_entity()],
        input_fn=scripted,
        output_fn=captured,
    )
    assert reviewed[0].decision.action == "approve"
    assert "entity User" in captured.text
    # Atom is re-rendered after [S] before the next prompt.
    # We assert this by checking the source excerpt appears at least twice.
    assert captured.text.count("Doctors and nurses") >= 2


def test_see_cedar_key_prints_property_reference() -> None:
    captured = _CaptureOutput()
    scripted = _ScriptedInput(["S", "A"])
    reviewed = interactive_review_loop(
        [_property()],
        input_fn=scripted,
        output_fn=captured,
    )
    assert reviewed[0].decision.action == "approve"
    assert "```cedar" in captured.text
    assert "principal == resource.owner" in captured.text


def test_see_cedar_key_explains_liveness_property_without_unknown_kind() -> None:
    captured = _CaptureOutput()
    scripted = _ScriptedInput(["S", "A"])
    reviewed = interactive_review_loop(
        [_liveness_property()],
        input_fn=scripted,
        output_fn=captured,
    )
    assert reviewed[0].decision.action == "approve"
    assert "Liveness property" in captured.text
    assert "unknown atom kind" not in captured.text


# ---------------------------------------------------------------------------
# [V] view patches — Stage 1 no-op message.
# ---------------------------------------------------------------------------


def test_view_patches_key_prints_stage1_no_op_message() -> None:
    captured = _CaptureOutput()
    scripted = _ScriptedInput(["V", "A"])
    reviewed = interactive_review_loop(
        [_entity()],
        input_fn=scripted,
        output_fn=captured,
    )
    assert reviewed[0].decision.action == "approve"
    assert "no §8.8 patches" in captured.text


def test_view_patches_key_prints_property_symbolic_log() -> None:
    captured = _CaptureOutput()
    scripted = _ScriptedInput(["V", "A"])
    reviewed = interactive_review_loop(
        [_property()],
        input_fn=scripted,
        output_fn=captured,
    )
    assert reviewed[0].decision.action == "approve"
    assert "type-correct: ok" in captured.text


# ---------------------------------------------------------------------------
# [Q] question — without LLM records, with LLM surfaces answer.
# ---------------------------------------------------------------------------


def test_question_without_llm_records_question() -> None:
    captured = _CaptureOutput()
    scripted = _ScriptedInput(["Q", "Should role be a Set<String>?", "A"])
    reviewed = interactive_review_loop(
        [_entity()],
        input_fn=scripted,
        output_fn=captured,
    )
    assert "Should role be a Set<String>?" in (
        reviewed[0].decision.edit_delta.get("questions", []) or []
    )[0]
    assert "no LLM connected" in captured.text


class _AnsweringLLM:
    """Minimal LLMClient stand-in: answers questions, proposes alternatives."""

    def __init__(
        self,
        *,
        answer: str = "",
        alternative: Any = None,
    ) -> None:
        self._answer = answer
        self._alt = alternative
        self.calls: list[dict[str, Any]] = []

    def answer_question_about_atom(self, atom: Any, question: str, spec_text: str) -> str:
        self.calls.append({"kind": "answer", "question": question, "atom": atom})
        return self._answer

    def propose_alternative_atom(
        self, rejected_atom: Any, user_reason: str, spec_text: str,
    ) -> Any:
        self.calls.append({"kind": "alternative", "reason": user_reason, "atom": rejected_atom})
        return self._alt


def test_question_with_llm_surfaces_answer_then_re_presents() -> None:
    captured = _CaptureOutput()
    scripted = _ScriptedInput(["Q", "What if a user has two roles?", "A"])
    llm = _AnsweringLLM(answer="The spec implies single role; if needed, edit to Set<String>.")
    reviewed = interactive_review_loop(
        [_entity()],
        llm=llm,  # type: ignore[arg-type]
        spec_text="...",
        input_fn=scripted,
        output_fn=captured,
    )
    assert reviewed[0].decision.action == "approve"
    assert "Agent: The spec implies single role" in captured.text
    assert llm.calls[0]["kind"] == "answer"


# ---------------------------------------------------------------------------
# [R] reject — without LLM records rejection, with LLM proposes alternative.
# ---------------------------------------------------------------------------


def test_reject_without_llm_records_rejection() -> None:
    captured = _CaptureOutput()
    scripted = _ScriptedInput(["R", "The name is wrong"])
    reviewed = interactive_review_loop(
        [_entity()],
        input_fn=scripted,
        output_fn=captured,
    )
    assert reviewed[0].decision.action == "reject"
    assert reviewed[0].decision.reason == "The name is wrong"


def test_reject_with_llm_replaces_atom_and_re_presents() -> None:
    """When the LLM proposes a replacement, the new atom is re-shown
    for review and approval, NOT auto-accepted."""
    captured = _CaptureOutput()
    replacement = EntityAtom(
        name="Person",                    # new name proposed by LLM
        rationale="renamed for clarity",
        plain_english_summary="A user-equivalent entity.",
        source_excerpt="Doctors and nurses ...",
    )
    llm = _AnsweringLLM(alternative=replacement)
    scripted = _ScriptedInput([
        "R", "The name is wrong",
        "A",                              # approve the LLM's replacement
    ])
    reviewed = interactive_review_loop(
        [_entity()],
        llm=llm,  # type: ignore[arg-type]
        spec_text="...",
        input_fn=scripted,
        output_fn=captured,
    )
    assert reviewed[0].atom.name == "Person"
    assert reviewed[0].decision.action == "approve"
    # The reject reason is captured in edit_delta even on final approve.
    assert reviewed[0].decision.edit_delta.get("reject_reason") == "The name is wrong"
    assert reviewed[0].decision.edit_delta.get("replaced_by_llm") is True


def test_reject_with_llm_returning_none_records_rejection() -> None:
    """If the LLM declines to propose, we record the rejection."""
    captured = _CaptureOutput()
    llm = _AnsweringLLM(alternative=None)
    scripted = _ScriptedInput(["R", "bad name"])
    reviewed = interactive_review_loop(
        [_entity()],
        llm=llm,  # type: ignore[arg-type]
        spec_text="...",
        input_fn=scripted,
        output_fn=captured,
    )
    assert reviewed[0].decision.action == "reject"
    assert "did not propose an alternative" in captured.text


# ---------------------------------------------------------------------------
# Unknown key — re-prompt without crashing.
# ---------------------------------------------------------------------------


def test_unknown_key_reprompts_without_advancing() -> None:
    captured = _CaptureOutput()
    scripted = _ScriptedInput(["X", "A"])
    reviewed = interactive_review_loop(
        [_entity()],
        input_fn=scripted,
        output_fn=captured,
    )
    assert reviewed[0].decision.action == "approve"
    assert "unknown key" in captured.text


def test_loop_handles_empty_input_as_unknown_key() -> None:
    captured = _CaptureOutput()
    scripted = _ScriptedInput(["", "A"])
    reviewed = interactive_review_loop(
        [_entity()],
        input_fn=scripted,
        output_fn=captured,
    )
    assert reviewed[0].decision.action == "approve"
