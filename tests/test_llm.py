"""Unit tests for ``autocedar.llm``.

Covers ``docs/HITL_STEP_C_PLAN.md`` §3 acceptance criterion 1 — the
``LLMClient`` constructs, accepts injected mock clients, and uses
prompt caching on the system+spec block.

A separate live test (``test_llm_live.py``) exercises the real
Anthropic API and is default-skipped.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from autocedar.atoms import (
    ActionAtom,
    AttributeAtom,
    EntityAtom,
    PropertyAtom,
    TypeAliasAtom,
)
from autocedar.llm import (
    DEFAULT_EFFORT,
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    LLMClient,
    PropertyAtomsResponse,
    SchemaAtomsResponse,
    SchemaFixResponse,
    _LLMActionAtom,
    _LLMAttributeAtom,
    _LLMContextAttribute,
    _LLMEntityAtom,
    _LLMPropertyAtom,
    _LLMTypeAliasAtom,
    _translate_atom,
)


# ---------------------------------------------------------------------------
# Mock SDK client.
# ---------------------------------------------------------------------------


class _FakeMessages:
    """Captures the kwargs from ``messages.parse`` and returns a fixture."""

    def __init__(self, response: Any) -> None:
        self.response = response
        self.last_kwargs: dict[str, Any] | None = None
        self.call_count = 0

    def parse(self, **kwargs: Any) -> Any:
        self.last_kwargs = kwargs
        self.call_count += 1
        return self.response


class _FakeAnthropic:
    """Drop-in test double for ``anthropic.Anthropic``."""

    def __init__(self, response: Any) -> None:
        self.messages = _FakeMessages(response)


class _GrammarTimeoutMessages:
    def __init__(self, fallback_text: str) -> None:
        self.fallback_text = fallback_text
        self.parse_count = 0
        self.create_count = 0
        self.create_kwargs: dict[str, Any] | None = None

    def parse(self, **kwargs: Any) -> Any:
        self.parse_count += 1
        raise RuntimeError("Error code: 400 - {'message': 'Grammar compilation timed out.'}")

    def create(self, **kwargs: Any) -> Any:
        self.create_count += 1
        self.create_kwargs = kwargs
        return SimpleNamespace(
            content=[SimpleNamespace(type="text", text=self.fallback_text)],
        )


class _GrammarTimeoutAnthropic:
    def __init__(self, fallback_text: str) -> None:
        self.messages = _GrammarTimeoutMessages(fallback_text)


def _make_response(parsed: Any) -> Any:
    """Construct a response object with the SDK's ``.parsed_output`` shape."""
    return SimpleNamespace(parsed_output=parsed)


# ---------------------------------------------------------------------------
# Construction + defaults.
# ---------------------------------------------------------------------------


def test_default_construction_uses_opus_4_7() -> None:
    """LLMClient defaults to claude-opus-4-7 per the claude-api skill."""
    # Inject a stub client so we don't actually hit anthropic.Anthropic().
    fake = _FakeAnthropic(_make_response(SchemaAtomsResponse(atoms=[])))
    client = LLMClient(client=fake)
    assert client._model == DEFAULT_MODEL == "claude-opus-4-7"


def test_construction_with_custom_model() -> None:
    fake = _FakeAnthropic(_make_response(SchemaAtomsResponse(atoms=[])))
    client = LLMClient(client=fake, model="claude-sonnet-4-6")
    assert client._model == "claude-sonnet-4-6"


def test_default_effort_is_high() -> None:
    fake = _FakeAnthropic(_make_response(SchemaAtomsResponse(atoms=[])))
    client = LLMClient(client=fake)
    assert client._effort == DEFAULT_EFFORT == "high"


def test_codex_provider_uses_codex_default_model(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeCodex:
        messages = _FakeMessages(_make_response(SchemaAtomsResponse(atoms=[])))

    monkeypatch.setenv("AUTOCEDAR_PROVIDER", "codex")
    monkeypatch.setenv("AUTOCEDAR_CODEX_MODEL", "gpt-test")
    monkeypatch.setattr("autocedar.llm.CodexExecClient", lambda: FakeCodex())

    client = LLMClient()

    assert client._provider == "codex"
    assert client._model == "gpt-test"


# ---------------------------------------------------------------------------
# Cache-control placement on the system+spec block.
# ---------------------------------------------------------------------------


def test_propose_schema_atoms_marks_spec_block_cache_controlled() -> None:
    """Per §2.3 of HITL_STEP_C_PLAN.md and the claude-api skill's
    prompt-caching guidance: the spec block must carry
    ``cache_control: {type: "ephemeral"}``.

    Defensive contract: this is the only ``cache_control`` annotation;
    no breakpoint on the per-turn ``messages`` block.
    """
    fake = _FakeAnthropic(_make_response(SchemaAtomsResponse(atoms=[])))
    client = LLMClient(client=fake)
    client.propose_schema_atoms("Doctors can read records.")

    kwargs = fake.messages.last_kwargs
    assert kwargs is not None
    system_blocks = kwargs["system"]

    # Exactly one block carries cache_control.
    cached = [b for b in system_blocks if b.get("cache_control")]
    assert len(cached) == 1
    assert cached[0]["cache_control"] == {"type": "ephemeral"}

    # The cached block is the spec block (contains the spec text).
    assert "Doctors can read records." in cached[0]["text"]

    # The per-turn message is uncached.
    for msg in kwargs["messages"]:
        if isinstance(msg.get("content"), list):
            for block in msg["content"]:
                assert "cache_control" not in block


def test_propose_schema_atoms_sends_adaptive_thinking_and_effort() -> None:
    """Per skill: Opus 4.7 + adaptive thinking + effort=high default."""
    fake = _FakeAnthropic(_make_response(SchemaAtomsResponse(atoms=[])))
    client = LLMClient(client=fake)
    client.propose_schema_atoms("...")

    kwargs = fake.messages.last_kwargs
    assert kwargs["thinking"] == {"type": "adaptive"}
    assert kwargs["output_config"]["effort"] == "high"
    # No legacy budget_tokens (removed on Opus 4.7 per skill).
    assert "budget_tokens" not in kwargs.get("thinking", {})


def test_propose_schema_atoms_uses_configured_model() -> None:
    fake = _FakeAnthropic(_make_response(SchemaAtomsResponse(atoms=[])))
    client = LLMClient(client=fake, model="claude-sonnet-4-6")
    client.propose_schema_atoms("...")
    assert fake.messages.last_kwargs["model"] == "claude-sonnet-4-6"


def test_propose_schema_atoms_uses_configured_max_tokens() -> None:
    fake = _FakeAnthropic(_make_response(SchemaAtomsResponse(atoms=[])))
    client = LLMClient(client=fake, max_tokens=4000)
    client.propose_schema_atoms("...")
    assert fake.messages.last_kwargs["max_tokens"] == 4000


# ---------------------------------------------------------------------------
# Pydantic → dataclass translation.
# ---------------------------------------------------------------------------


def test_translate_entity_atom() -> None:
    llm = _LLMEntityAtom(
        kind="entity",
        name="User",
        rationale="principal",
        plain_english_summary="The principal",
        source_excerpt="Doctors and nurses ...",
        members_of=[],
        enum_values=None,
    )
    atom = _translate_atom(llm)
    assert isinstance(atom, EntityAtom)
    assert atom.name == "User"
    assert atom.enum_values is None


def test_translate_attribute_atom() -> None:
    llm = _LLMAttributeAtom(
        kind="attribute",
        name="User__role",
        rationale="single string role",
        plain_english_summary="Each user has one role.",
        source_excerpt="...",
        on_entity="User",
        field_name="role",
        cedar_type="String",
        alternatives_considered=["Set<String>"],
    )
    atom = _translate_atom(llm)
    assert isinstance(atom, AttributeAtom)
    assert atom.on_entity == "User"
    assert atom.field_name == "role"
    assert atom.cedar_type == "String"
    assert "Set<String>" in atom.alternatives_considered


def test_translate_action_atom_with_context_attributes() -> None:
    """Context attributes inline on the LLM atom translate into
    a ``dict[str, AttributeAtom]`` on the dataclass."""
    llm = _LLMActionAtom(
        kind="action",
        name="bulkExport",
        rationale="bulk export action",
        plain_english_summary="bulk export",
        source_excerpt="...",
        principal_types=["User"],
        resource_types=["Record"],
        context_attributes=[
            _LLMContextAttribute(
                field_name="requestsPerMinute",
                cedar_type="Long",
                rationale="rate-limit counter",
            ),
        ],
        parent_groups=[],
    )
    atom = _translate_atom(llm)
    assert isinstance(atom, ActionAtom)
    assert atom.principal_types == ["User"]
    assert "requestsPerMinute" in atom.context_attributes
    ctx_attr = atom.context_attributes["requestsPerMinute"]
    assert isinstance(ctx_attr, AttributeAtom)
    assert ctx_attr.on_entity == ""  # context, not an entity
    assert ctx_attr.cedar_type == "Long"


def test_translate_type_alias_atom() -> None:
    llm = _LLMTypeAliasAtom(
        kind="type_alias",
        name="Address",
        rationale="reusable shape",
        plain_english_summary="An address record.",
        source_excerpt="...",
        cedar_type="{ street: String, zip: String }",
    )
    atom = _translate_atom(llm)
    assert isinstance(atom, TypeAliasAtom)
    assert atom.cedar_type == "{ street: String, zip: String }"


# ---------------------------------------------------------------------------
# propose_schema_atoms — end-to-end with mocked LLM.
# ---------------------------------------------------------------------------


def test_propose_schema_atoms_returns_translated_dataclasses() -> None:
    fake_response = _make_response(
        SchemaAtomsResponse(
            atoms=[
                _LLMEntityAtom(
                    kind="entity",
                    name="User",
                    rationale="principal",
                    plain_english_summary="user",
                    source_excerpt="...",
                ),
                _LLMAttributeAtom(
                    kind="attribute",
                    name="User__role",
                    rationale="...",
                    plain_english_summary="...",
                    source_excerpt="...",
                    on_entity="User",
                    field_name="role",
                    cedar_type="String",
                ),
            ],
        ),
    )
    fake = _FakeAnthropic(fake_response)
    client = LLMClient(client=fake)
    atoms = client.propose_schema_atoms("Spec text.")
    assert len(atoms) == 2
    assert isinstance(atoms[0], EntityAtom)
    assert isinstance(atoms[1], AttributeAtom)


def test_propose_schema_atoms_calls_llm_exactly_once() -> None:
    fake = _FakeAnthropic(_make_response(SchemaAtomsResponse(atoms=[])))
    client = LLMClient(client=fake)
    client.propose_schema_atoms("spec")
    assert fake.messages.call_count == 1


# ---------------------------------------------------------------------------
# propose_property_atoms — Stage 2 with mocked LLM.
# ---------------------------------------------------------------------------


def test_propose_property_atoms_returns_translated_dataclasses() -> None:
    fake_response = _make_response(
        PropertyAtomsResponse(
            atoms=[
                _LLMPropertyAtom(
                    name="owner_only_read",
                    rationale="safety bound",
                    plain_english_summary="Only owners can read.",
                    source_excerpt="Owners can read their own resources.",
                    constraint_type="ceiling",
                    action="read",
                    principal_types=["User"],
                    resource_types=["Resource"],
                    reference_cedar=(
                        'permit (principal is User, action == Action::"read", resource is Resource)\n'
                        "when { principal == resource.owner };"
                    ),
                ),
            ],
        ),
    )
    fake = _FakeAnthropic(fake_response)
    client = LLMClient(client=fake)
    atoms = client.propose_property_atoms("Owners can read.", "entity User;")

    assert len(atoms) == 1
    assert isinstance(atoms[0], PropertyAtom)
    assert atoms[0].constraint_type == "ceiling"
    assert atoms[0].action == "read"


def test_propose_property_atoms_includes_schema_in_user_turn() -> None:
    fake = _FakeAnthropic(_make_response(PropertyAtomsResponse(atoms=[])))
    client = LLMClient(client=fake)
    client.propose_property_atoms("Owners can read.", "entity User;")

    kwargs = fake.messages.last_kwargs
    assert kwargs["output_format"] is PropertyAtomsResponse
    assert "```cedarschema\nentity User;\n```" in kwargs["messages"][0]["content"]


def test_property_atomization_prompt_guards_scenario2_override_shape() -> None:
    fake = _FakeAnthropic(_make_response(PropertyAtomsResponse(atoms=[])))
    client = LLMClient(client=fake)
    spec = (
        "A user can view and comment on a ticket if they are a member of the "
        "ticket's team. Closed tickets cannot be commented on by anyone. "
        "The no-one-comments rule overrides the permission."
    )
    schema = (
        "entity Team;\n"
        "entity User in [Team];\n"
        "entity Ticket { team: Team, status: String, };\n"
    )

    client.propose_property_atoms(spec, schema)

    kwargs = fake.messages.last_kwargs
    system_text = "\n".join(block["text"] for block in kwargs["system"])
    assert "Prefer `disjointness` for explicit deny/override language" in system_text
    assert "closed tickets cannot be commented on" in system_text
    assert "Do not emit duplicate liveness atoms" in system_text
    assert spec in system_text
    assert f"```cedarschema\n{schema}\n```" in kwargs["messages"][0]["content"]


def test_propose_alternative_property_atom_includes_rejection_context() -> None:
    fake_response = _make_response(
        PropertyAtomsResponse(
            atoms=[
                _LLMPropertyAtom(
                    name="owner_floor_read",
                    rationale="minimum owner permission",
                    plain_english_summary="Owners must be able to read.",
                    source_excerpt="Owners can read their own resources.",
                    constraint_type="floor",
                    action="read",
                    principal_types=["User"],
                    resource_types=["Resource"],
                    reference_cedar=(
                        'permit (principal is User, action == Action::"read", resource is Resource)\n'
                        "when { principal == resource.owner };"
                    ),
                ),
            ],
        ),
    )
    fake = _FakeAnthropic(fake_response)
    client = LLMClient(client=fake)
    rejected = PropertyAtom(
        name="owner_ceiling_read",
        rationale="bad direction",
        plain_english_summary="Only owners can read.",
        source_excerpt="Owners can read their own resources.",
        constraint_type="ceiling",
        action="read",
        principal_types=["User"],
        resource_types=["Resource"],
        reference_cedar='permit (principal, action == Action::"read", resource);',
    )

    replacement = client.propose_alternative_property_atom(
        rejected,
        "this should be a floor, not a ceiling",
        "Owners can read their own resources.",
        "entity User;",
        prior_atoms=[rejected],
    )

    assert replacement is not None
    assert replacement.name == "owner_floor_read"
    assert replacement.constraint_type == "floor"
    kwargs = fake.messages.last_kwargs
    assert kwargs["output_format"] is PropertyAtomsResponse
    user_turn = kwargs["messages"][0]["content"]
    assert "```cedarschema\nentity User;\n```" in user_turn
    assert "this should be a floor, not a ceiling" in user_turn
    assert "owner_ceiling_read" in user_turn


def test_propose_property_atoms_falls_back_when_grammar_compilation_times_out() -> None:
    fallback = """
    ```json
    {
      "atoms": [
        {
          "name": "owner_only_read",
          "rationale": "safety bound",
          "plain_english_summary": "Only owners can read.",
          "source_excerpt": "Owners can read their own resources.",
          "constraint_type": "ceiling",
          "action": "read",
          "principal_types": ["User"],
          "resource_types": ["Resource"],
          "reference_cedar": "permit (principal, action, resource);",
          "examples_adversarial": [],
          "alternatives_considered": [],
          "rate_limit_window": null,
          "rate_limit_threshold": null,
          "rate_limit_counter_attr": null,
          "disjoint_with": null,
          "disjoint_target_body": null
        }
      ]
    }
    ```
    """
    fake = _GrammarTimeoutAnthropic(fallback)
    client = LLMClient(client=fake)

    atoms = client.propose_property_atoms("Owners can read.", "entity User;")

    assert len(atoms) == 1
    assert atoms[0].name == "owner_only_read"
    assert fake.messages.parse_count == 1
    assert fake.messages.create_count == 1
    assert fake.messages.create_kwargs is not None
    assert "The structured-output grammar compiler timed out" in fake.messages.create_kwargs[
        "messages"
    ][0]["content"]


# ---------------------------------------------------------------------------
# fix_schema — bounded LLM retry on validate failure.
# ---------------------------------------------------------------------------


def test_fix_schema_returns_corrected_text() -> None:
    fake_response = _make_response(
        SchemaFixResponse(
            fixed_schema_text="entity User;\n",
            explanation="Removed the malformed members_of clause.",
        ),
    )
    fake = _FakeAnthropic(fake_response)
    client = LLMClient(client=fake)
    fixed = client.fix_schema(
        schema_text="entity User in [;",
        cedar_error_message="parse error at position 16",
        spec_text="Users have roles.",
    )
    assert fixed == "entity User;\n"
    # Cache-control still on the spec block.
    cached = [b for b in fake.messages.last_kwargs["system"] if b.get("cache_control")]
    assert len(cached) == 1


def test_fix_schema_includes_error_text_in_user_turn() -> None:
    """The fix call must surface the cedar validate error to the LLM."""
    fake_response = _make_response(
        SchemaFixResponse(fixed_schema_text="entity User;\n", explanation=""),
    )
    fake = _FakeAnthropic(fake_response)
    client = LLMClient(client=fake)
    client.fix_schema(
        schema_text="entity User in [;",
        cedar_error_message="EXPECTED IDENTIFIER",
        spec_text="...",
    )
    user_msg = fake.messages.last_kwargs["messages"][0]
    assert "EXPECTED IDENTIFIER" in user_msg["content"]
