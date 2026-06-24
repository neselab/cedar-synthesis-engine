"""Tests for ``autocedar.schema_atomizer`` — Stage 1 atomizer.

Covers acceptance criterion 3 of ``docs/HITL_STEP_C_PLAN.md`` §3 —
``compose_and_validate`` runs cedar validate; on failure asks the LLM
to fix; loops up to 3 attempts.
"""

from __future__ import annotations

import os
import textwrap
from pathlib import Path
from typing import Any

import pytest

from autocedar.atoms import (
    ActionAtom,
    AttributeAtom,
    EntityAtom,
    SchemaDraft,
    TypeAliasAtom,
)
from autocedar.grounding import CEDAR_PATH
from autocedar.schema_atomizer import (
    apply_schema_atoms_to_text,
    cedar_validate_schema,
    compose_and_validate,
    compose_schema,
    propose_schema_atoms,
    route_atom_into_draft,
)

_HAVE_CEDAR = os.path.isfile(CEDAR_PATH) and os.access(CEDAR_PATH, os.X_OK)
requires_cedar = pytest.mark.skipif(not _HAVE_CEDAR, reason="cedar not available")


# ---------------------------------------------------------------------------
# compose_schema (extends Step B coverage).
# ---------------------------------------------------------------------------

def test_compose_schema_renders_entity_with_attributes() -> None:
    draft = SchemaDraft(
        entities={
            "User": EntityAtom(
                name="User",
                rationale="...",
                plain_english_summary="...",
                source_excerpt="...",
                attributes={
                    "role": AttributeAtom(
                        name="User__role",
                        rationale="...",
                        plain_english_summary="...",
                        source_excerpt="...",
                        on_entity="User",
                        field_name="role",
                        cedar_type="String",
                    ),
                },
            ),
        },
    )
    text = compose_schema(draft)
    assert "entity User" in text
    assert "role: String" in text


def test_compose_schema_orders_aliases_entities_actions() -> None:
    draft = SchemaDraft(
        entities={
            "User": EntityAtom(
                name="User", rationale="...",
                plain_english_summary="...", source_excerpt="...",
            ),
        },
        actions={
            "read": ActionAtom(
                name="read", rationale="...",
                plain_english_summary="...", source_excerpt="...",
                principal_types=["User"], resource_types=["User"],
            ),
        },
        type_aliases={
            "Address": TypeAliasAtom(
                name="Address", rationale="...",
                plain_english_summary="...", source_excerpt="...",
                cedar_type="{ street: String }",
            ),
        },
    )
    text = compose_schema(draft)
    # type alias appears before the entity which appears before the action
    alias_idx = text.index("type Address")
    entity_idx = text.index("entity User")
    action_idx = text.index("action read")
    assert alias_idx < entity_idx < action_idx


# ---------------------------------------------------------------------------
# route_atom_into_draft.
# ---------------------------------------------------------------------------

def test_route_attribute_inserts_into_owner_entity() -> None:
    draft = SchemaDraft()
    user = EntityAtom(
        name="User", rationale="...",
        plain_english_summary="...", source_excerpt="...",
    )
    role = AttributeAtom(
        name="User__role", rationale="...",
        plain_english_summary="...", source_excerpt="...",
        on_entity="User", field_name="role", cedar_type="String",
    )
    route_atom_into_draft(user, draft)
    route_atom_into_draft(role, draft)
    assert draft.entities["User"].attributes["role"].cedar_type == "String"


def test_route_attribute_silently_drops_when_owner_missing() -> None:
    """When an AttributeAtom's owner entity hasn't been added yet, the
    attribute is silently dropped. The pipeline's ordering invariant
    is what guarantees this doesn't happen in practice."""
    draft = SchemaDraft()
    orphan = AttributeAtom(
        name="Missing__field", rationale="...",
        plain_english_summary="...", source_excerpt="...",
        on_entity="Missing", field_name="field", cedar_type="String",
    )
    route_atom_into_draft(orphan, draft)
    assert "Missing" not in draft.entities


def test_apply_schema_atoms_to_text_adds_attribute_to_bare_entity() -> None:
    schema = "entity Semester;\n"
    repaired = apply_schema_atoms_to_text(
        schema,
        [
            AttributeAtom(
                name="Semester__isCurrent",
                rationale="current marker",
                plain_english_summary="Current semester marker.",
                source_excerpt="current semester",
                on_entity="Semester",
                field_name="isCurrent",
                cedar_type="Bool",
            ),
        ],
    )

    assert repaired == "entity Semester {\n    isCurrent: Bool,\n};\n"


def test_apply_schema_atoms_to_text_adds_attribute_to_existing_entity() -> None:
    schema = textwrap.dedent("""\
        entity Semester {
            name: String,
        };
    """)
    repaired = apply_schema_atoms_to_text(
        schema,
        [
            AttributeAtom(
                name="Semester__isUpcoming",
                rationale="upcoming marker",
                plain_english_summary="Upcoming semester marker.",
                source_excerpt="upcoming semester",
                on_entity="Semester",
                field_name="isUpcoming",
                cedar_type="Bool",
            ),
        ],
    )

    assert repaired is not None
    assert "name: String" in repaired
    assert "isUpcoming: Bool" in repaired


def test_apply_schema_atoms_to_text_adds_context_to_existing_action() -> None:
    schema = textwrap.dedent("""\
        entity User;

        entity Document;

        action read appliesTo {
            principal: [User],
            resource: [Document],
        };
    """)
    repaired = apply_schema_atoms_to_text(
        schema,
        [
            ActionAtom(
                name="read",
                rationale="read action context repair",
                plain_english_summary="Read action.",
                source_excerpt="from campus LAN",
                principal_types=["User"],
                resource_types=["Document"],
                context_attributes={
                    "isCampusLan": AttributeAtom(
                        name="read__isCampusLan",
                        rationale="network boundary",
                        plain_english_summary="Campus LAN request marker.",
                        source_excerpt="campus LAN",
                        on_entity="",
                        field_name="isCampusLan",
                        cedar_type="Bool",
                    ),
                },
            ),
        ],
    )

    assert repaired is not None
    assert "context: {" in repaired
    assert "isCampusLan: Bool" in repaired


def test_apply_schema_atoms_to_text_returns_none_for_missing_owner() -> None:
    repaired = apply_schema_atoms_to_text(
        "entity User;\n",
        [
            AttributeAtom(
                name="Semester__isCurrent",
                rationale="current marker",
                plain_english_summary="Current semester marker.",
                source_excerpt="current semester",
                on_entity="Semester",
                field_name="isCurrent",
                cedar_type="Bool",
            ),
        ],
    )

    assert repaired is None


# ---------------------------------------------------------------------------
# propose_schema_atoms — wires through to LLMClient.
# ---------------------------------------------------------------------------

class _RecordingLLM:
    """Minimal LLMClient stand-in: records the call, returns a canned list."""

    def __init__(self, atoms_to_return: list[Any]) -> None:
        self._return = atoms_to_return
        self.called_with: str | None = None

    def propose_schema_atoms(self, spec_text: str) -> list[Any]:
        self.called_with = spec_text
        return self._return


def test_propose_schema_atoms_delegates_to_llm() -> None:
    expected = [
        EntityAtom(
            name="User", rationale="...",
            plain_english_summary="...", source_excerpt="...",
        ),
    ]
    llm = _RecordingLLM(expected)
    atoms = propose_schema_atoms("spec text here", llm)  # type: ignore[arg-type]
    assert atoms == expected
    assert llm.called_with == "spec text here"


# ---------------------------------------------------------------------------
# cedar_validate_schema — integration with real cedar binary.
# ---------------------------------------------------------------------------

@requires_cedar
def test_validate_passes_on_well_formed_schema(tmp_path: Path) -> None:
    schema = tmp_path / "good.cedarschema"
    schema.write_text(textwrap.dedent("""\
        entity User {
            role: String,
        };
        entity Resource {
            owner: User,
        };
        action read appliesTo {
            principal: [User],
            resource: [Resource],
        };
    """))
    passed, err = cedar_validate_schema(schema)
    assert passed, err


@requires_cedar
def test_validate_fails_on_malformed_schema(tmp_path: Path) -> None:
    schema = tmp_path / "bad.cedarschema"
    schema.write_text("entity User in [;\n")
    passed, err = cedar_validate_schema(schema)
    assert not passed
    assert "error" in err.lower() or "unexpected" in err.lower()


# ---------------------------------------------------------------------------
# compose_and_validate — the LLM-fix loop.
# ---------------------------------------------------------------------------

def _good_draft() -> SchemaDraft:
    """A draft that composes to a cedar-validate-passing schema."""
    user = EntityAtom(
        name="User", rationale="...",
        plain_english_summary="...", source_excerpt="...",
        attributes={
            "role": AttributeAtom(
                name="User__role", rationale="...",
                plain_english_summary="...", source_excerpt="...",
                on_entity="User", field_name="role", cedar_type="String",
            ),
        },
    )
    res = EntityAtom(
        name="Resource", rationale="...",
        plain_english_summary="...", source_excerpt="...",
    )
    action = ActionAtom(
        name="read", rationale="...",
        plain_english_summary="...", source_excerpt="...",
        principal_types=["User"], resource_types=["Resource"],
    )
    return SchemaDraft(entities={"User": user, "Resource": res}, actions={"read": action})


def _bad_draft() -> SchemaDraft:
    """A draft that composes to a malformed schema.

    The Cedar grammar rejects `entity X in []` with the trailing comma
    we synthesize here from an attribute whose cedar_type is invalid.
    """
    return SchemaDraft(
        entities={
            "User": EntityAtom(
                name="User", rationale="...",
                plain_english_summary="...", source_excerpt="...",
                attributes={
                    "broken": AttributeAtom(
                        name="User__broken", rationale="...",
                        plain_english_summary="...", source_excerpt="...",
                        on_entity="User", field_name="broken",
                        cedar_type="!!INVALID_TYPE!!",  # invalid
                    ),
                },
            ),
        },
    )


@requires_cedar
def test_compose_and_validate_succeeds_on_first_try(tmp_path: Path) -> None:
    schema_path = tmp_path / "schema.cedarschema"
    result = compose_and_validate(_good_draft(), schema_path, llm=None)
    assert result.succeeded
    assert len(result.attempts) == 1
    assert result.attempts[0].validator_passed
    assert result.schema_text == schema_path.read_text()


@requires_cedar
def test_compose_and_validate_fails_without_llm(tmp_path: Path) -> None:
    """When the schema is malformed and no LLM is provided, the call
    returns succeeded=False without any retries — used by tests that
    want to inspect the validator path in isolation."""
    schema_path = tmp_path / "schema.cedarschema"
    result = compose_and_validate(_bad_draft(), schema_path, llm=None)
    assert not result.succeeded
    assert len(result.attempts) == 1
    assert not result.attempts[0].validator_passed
    assert result.attempts[0].validator_error  # error message captured


class _ScriptedFixLLM:
    """LLM stub that returns a hard-coded fixed schema on fix_schema()."""

    def __init__(self, fixed_schema: str) -> None:
        self._fixed = fixed_schema
        self.fix_calls: list[dict[str, Any]] = []

    def fix_schema(
        self, schema_text: str, cedar_error_message: str, spec_text: str,
    ) -> str:
        self.fix_calls.append(
            {
                "schema_text": schema_text,
                "error": cedar_error_message,
                "spec_text": spec_text,
            },
        )
        return self._fixed


@requires_cedar
def test_compose_and_validate_succeeds_on_one_llm_fix(tmp_path: Path) -> None:
    """Bad draft → cedar fails → LLM returns a good schema → succeeds."""
    schema_path = tmp_path / "schema.cedarschema"
    good_schema = textwrap.dedent("""\
        entity User {
            role: String,
        };
        entity Resource;
        action read appliesTo {
            principal: [User],
            resource: [Resource],
        };
    """)
    llm = _ScriptedFixLLM(fixed_schema=good_schema)
    result = compose_and_validate(
        _bad_draft(), schema_path,
        llm=llm,  # type: ignore[arg-type]
        spec_text="Users have roles. Users can read resources.",
        max_attempts=3,
    )
    assert result.succeeded
    # Two attempts: the bad initial compose + the LLM-fixed retry.
    assert len(result.attempts) == 2
    assert not result.attempts[0].validator_passed
    assert result.attempts[0].llm_was_called
    assert result.attempts[1].validator_passed
    # LLM was called once with the cedar error.
    assert len(llm.fix_calls) == 1
    assert llm.fix_calls[0]["error"]
    assert llm.fix_calls[0]["spec_text"] == "Users have roles. Users can read resources."


@requires_cedar
def test_compose_and_validate_exhausts_attempts(tmp_path: Path) -> None:
    """If the LLM never returns a valid schema, the loop bounds at
    max_attempts and returns succeeded=False with the full log."""
    schema_path = tmp_path / "schema.cedarschema"
    llm = _ScriptedFixLLM(fixed_schema="entity Broken in [;\n")  # always bad
    result = compose_and_validate(
        _bad_draft(), schema_path,
        llm=llm,  # type: ignore[arg-type]
        spec_text="...",
        max_attempts=3,
    )
    assert not result.succeeded
    # Three attempts: the original + two LLM retries.
    # On the third (max) attempt, llm.fix_schema is NOT called because
    # the loop already knows it has no more retries to spend.
    assert len(result.attempts) == 3
    assert all(not a.validator_passed for a in result.attempts)
    # LLM was called twice (after attempt 1 and after attempt 2).
    assert len(llm.fix_calls) == 2


@requires_cedar
def test_compose_and_validate_strips_code_fence_from_llm_output(tmp_path: Path) -> None:
    """The LLM sometimes wraps output in a Markdown fence despite the
    Pydantic schema. ``_strip_code_fence`` removes it before write."""
    schema_path = tmp_path / "schema.cedarschema"
    good = textwrap.dedent("""\
        ```cedarschema
        entity User;
        entity Resource;
        action read appliesTo { principal: [User], resource: [Resource] };
        ```""")
    llm = _ScriptedFixLLM(fixed_schema=good)
    result = compose_and_validate(
        _bad_draft(), schema_path,
        llm=llm,  # type: ignore[arg-type]
        spec_text="...",
        max_attempts=3,
    )
    assert result.succeeded
    # On disk: no leading ```cedarschema fence.
    written = schema_path.read_text()
    assert not written.lstrip().startswith("```")
    assert "entity User;" in written
