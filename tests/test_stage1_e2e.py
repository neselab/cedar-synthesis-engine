"""End-to-end Stage 1 integration test.

Covers acceptance criterion 5 of ``docs/HITL_STEP_C_PLAN.md`` §3:
with a mocked LLM, a scripted reviewer, and a prose spec — Stage 1
produces a ``cedar validate``-passing schema written to disk.

Exercises the full Step C path:
    spec → LLMClient.propose_schema_atoms (mocked SDK)
         → interactive_review_loop (scripted input)
         → route_atom_into_draft
         → compose_and_validate (real cedar validate)
"""

from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Iterable

import pytest

from autocedar.atoms import (
    ActionAtom,
    AttributeAtom,
    EntityAtom,
    SchemaDraft,
)
from autocedar.grounding import CEDAR_PATH
from autocedar.llm import (
    LLMClient,
    SchemaAtomsResponse,
    _LLMActionAtom,
    _LLMAttributeAtom,
    _LLMContextAttribute,
    _LLMEntityAtom,
)
from autocedar.schema_atomizer import (
    cedar_validate_schema,
    compose_and_validate,
    propose_schema_atoms,
    route_atom_into_draft,
)
from autocedar.ui.terminal import interactive_review_loop

_HAVE_CEDAR = os.path.isfile(CEDAR_PATH) and os.access(CEDAR_PATH, os.X_OK)
requires_cedar = pytest.mark.skipif(not _HAVE_CEDAR, reason="cedar not available")


# ---------------------------------------------------------------------------
# Test doubles for the Anthropic SDK and the terminal I/O.
# ---------------------------------------------------------------------------


class _FakeMessages:
    def __init__(self, response: Any) -> None:
        self.response = response

    def parse(self, **kwargs: Any) -> Any:
        return self.response


class _FakeAnthropic:
    def __init__(self, response: Any) -> None:
        self.messages = _FakeMessages(response)


class _ScriptedInput:
    def __init__(self, lines: Iterable[str]) -> None:
        self._iter = iter(list(lines))

    def __call__(self, prompt: str = "") -> str:
        return next(self._iter)


# ---------------------------------------------------------------------------
# Fixture: LLM response with a complete, well-formed schema proposal.
# ---------------------------------------------------------------------------


def _canned_llm_response() -> Any:
    """A hand-crafted SchemaAtomsResponse that maps to a valid Cedar schema.

    The spec implicitly modeled: "Users can read records." We propose
    five atoms: User entity, User.role attribute, Record entity,
    Record.owner attribute, read action.
    """
    atoms = [
        _LLMEntityAtom(
            kind="entity",
            name="User",
            rationale="The principal type for every request.",
            plain_english_summary="A person who reads records.",
            source_excerpt="Users can read records.",
        ),
        _LLMAttributeAtom(
            kind="attribute",
            name="User__role",
            rationale="Spec uses 'role' to gate access.",
            plain_english_summary="The user's role.",
            source_excerpt="Users can read records.",
            on_entity="User",
            field_name="role",
            cedar_type="String",
        ),
        _LLMEntityAtom(
            kind="entity",
            name="Record",
            rationale="The resource being read.",
            plain_english_summary="A record.",
            source_excerpt="Users can read records.",
        ),
        _LLMAttributeAtom(
            kind="attribute",
            name="Record__owner",
            rationale="Records have an owner.",
            plain_english_summary="The record's owner.",
            source_excerpt="Users can read records.",
            on_entity="Record",
            field_name="owner",
            cedar_type="User",
        ),
        _LLMActionAtom(
            kind="action",
            name="read",
            rationale="The read action.",
            plain_english_summary="Read a record.",
            source_excerpt="Users can read records.",
            principal_types=["User"],
            resource_types=["Record"],
            context_attributes=[],
        ),
    ]
    return SimpleNamespace(parsed_output=SchemaAtomsResponse(atoms=atoms))


# ---------------------------------------------------------------------------
# End-to-end test.
# ---------------------------------------------------------------------------


@requires_cedar
def test_stage1_end_to_end_produces_validating_schema(tmp_path: Path) -> None:
    """Full Stage 1: mocked LLM proposes 5 atoms; scripted reviewer
    auto-approves each; compose + cedar validate succeed; the
    resulting schema is written to disk."""
    spec_text = "Users can read records."

    # Step 1 — LLM proposes atoms.
    fake = _FakeAnthropic(_canned_llm_response())
    llm = LLMClient(client=fake)
    atoms = propose_schema_atoms(spec_text, llm)
    assert len(atoms) == 5
    assert any(isinstance(a, EntityAtom) and a.name == "User" for a in atoms)
    assert any(isinstance(a, ActionAtom) and a.name == "read" for a in atoms)

    # Step 2 — interactive review (scripted auto-approve).
    scripted_keys = _ScriptedInput(["A"] * len(atoms))
    captured: list[str] = []
    reviewed = interactive_review_loop(
        atoms,
        llm=None,  # no LLM needed for pure approve flow
        spec_text=spec_text,
        input_fn=scripted_keys,
        output_fn=captured.append,
    )
    assert [r.decision.action for r in reviewed] == ["approve"] * 5
    assert all(r.decision.intent_acknowledged_by_user for r in reviewed)

    # Step 3 — route approved atoms into a draft.
    draft = SchemaDraft()
    for r in reviewed:
        route_atom_into_draft(r.atom, draft)
    assert "User" in draft.entities
    assert "Record" in draft.entities
    assert "read" in draft.actions
    # Attribute atoms landed under their owner entities.
    assert draft.entities["User"].attributes["role"].cedar_type == "String"
    assert draft.entities["Record"].attributes["owner"].cedar_type == "User"

    # Step 4 — compose + validate against the real cedar binary.
    schema_path = tmp_path / "schema.cedarschema"
    result = compose_and_validate(
        draft, schema_path, llm=None, spec_text=spec_text,
    )
    assert result.succeeded, f"compose_and_validate failed: {result.attempts}"
    assert result.attempts[-1].validator_passed
    # The schema is on disk.
    assert schema_path.exists()

    # Final sanity check: rerun cedar validate against the written file.
    passed, err = cedar_validate_schema(schema_path)
    assert passed, err


@requires_cedar
def test_stage1_e2e_with_action_context_attributes(tmp_path: Path) -> None:
    """A more complex E2E: action with inline context attributes.

    Covers the LLM→dataclass translation path for context attributes
    and ensures the composed schema is still cedar-validate-passing.
    """
    spec_text = "Users can bulk-export records up to 100 times per minute."

    atoms_response = SchemaAtomsResponse(
        atoms=[
            _LLMEntityAtom(
                kind="entity",
                name="User",
                rationale="...",
                plain_english_summary="...",
                source_excerpt="Users can bulk-export records ...",
            ),
            _LLMEntityAtom(
                kind="entity",
                name="Record",
                rationale="...",
                plain_english_summary="...",
                source_excerpt="...",
            ),
            _LLMActionAtom(
                kind="action",
                name="bulkExport",
                rationale="...",
                plain_english_summary="Bulk export records.",
                source_excerpt="Users can bulk-export records ...",
                principal_types=["User"],
                resource_types=["Record"],
                context_attributes=[
                    _LLMContextAttribute(
                        field_name="requestsPerMinute",
                        cedar_type="Long",
                        rationale="rate limit counter",
                    ),
                ],
            ),
        ],
    )
    fake = _FakeAnthropic(SimpleNamespace(parsed_output=atoms_response))
    llm = LLMClient(client=fake)
    atoms = propose_schema_atoms(spec_text, llm)

    scripted_keys = _ScriptedInput(["A"] * len(atoms))
    captured: list[str] = []
    reviewed = interactive_review_loop(
        atoms, llm=None, input_fn=scripted_keys, output_fn=captured.append,
    )

    draft = SchemaDraft()
    for r in reviewed:
        route_atom_into_draft(r.atom, draft)

    # Action received the inline context attributes correctly.
    bulk_export = draft.actions["bulkExport"]
    assert "requestsPerMinute" in bulk_export.context_attributes
    ctx = bulk_export.context_attributes["requestsPerMinute"]
    assert isinstance(ctx, AttributeAtom)
    assert ctx.cedar_type == "Long"
    assert ctx.on_entity == ""

    schema_path = tmp_path / "schema.cedarschema"
    result = compose_and_validate(draft, schema_path, llm=None, spec_text=spec_text)
    assert result.succeeded, f"compose_and_validate failed: {result.attempts}"
    # The composed schema includes the context block for bulkExport.
    schema_text = schema_path.read_text()
    assert "bulkExport" in schema_text
    assert "requestsPerMinute" in schema_text


@requires_cedar
def test_stage1_e2e_with_user_edit_changes_attribute_type(tmp_path: Path) -> None:
    """User edits an attribute's cedar_type via [E]; the edited atom
    flows through to compose_and_validate and ends up in the schema."""
    spec_text = "Users have roles."

    atoms_response = SchemaAtomsResponse(
        atoms=[
            _LLMEntityAtom(
                kind="entity",
                name="User",
                rationale="...",
                plain_english_summary="...",
                source_excerpt="Users have roles.",
            ),
            _LLMAttributeAtom(
                kind="attribute",
                name="User__role",
                rationale="...",
                plain_english_summary="...",
                source_excerpt="Users have roles.",
                on_entity="User",
                field_name="role",
                cedar_type="String",
            ),
            _LLMEntityAtom(
                kind="entity",
                name="Resource",
                rationale="...",
                plain_english_summary="...",
                source_excerpt="...",
            ),
            _LLMActionAtom(
                kind="action",
                name="read",
                rationale="...",
                plain_english_summary="...",
                source_excerpt="...",
                principal_types=["User"],
                resource_types=["Resource"],
            ),
        ],
    )
    fake = _FakeAnthropic(SimpleNamespace(parsed_output=atoms_response))
    llm = LLMClient(client=fake)
    atoms = propose_schema_atoms(spec_text, llm)

    # Scripted input: approve User; on the role attribute, edit
    # cedar_type from String to Set<String>; approve everything else.
    scripted = _ScriptedInput([
        "A",                              # User entity
        "E", "cedar_type=Set<String>", "A",  # role attribute
        "A",                              # Resource entity
        "A",                              # read action
    ])
    captured: list[str] = []
    reviewed = interactive_review_loop(
        atoms, llm=None, input_fn=scripted, output_fn=captured.append,
    )

    draft = SchemaDraft()
    for r in reviewed:
        route_atom_into_draft(r.atom, draft)

    # The edit flowed through.
    assert draft.entities["User"].attributes["role"].cedar_type == "Set<String>"

    schema_path = tmp_path / "schema.cedarschema"
    result = compose_and_validate(draft, schema_path, llm=None, spec_text=spec_text)
    assert result.succeeded, f"compose_and_validate failed: {result.attempts}"
    assert "Set<String>" in schema_path.read_text()
