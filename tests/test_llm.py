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
from autocedar.codex_auth import DEFAULT_CODEX_MODEL
from autocedar.llm import (
    DEFAULT_ANTHROPIC_MODEL,
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
    _LLMRequiredSchemaSupport,
    _LLMTypeAliasAtom,
    _property_coverage_instruction,
    _translate_atom,
    _translate_property_atom,
    create_runtime_backend,
)
from autocedar.providers import ResolvedProviderConfig


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


def test_default_construction_uses_codex(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    """LLMClient defaults to the local Codex OAuth provider."""
    monkeypatch.delenv("AUTOCEDAR_PROVIDER", raising=False)
    monkeypatch.delenv("AUTOCEDAR_CODEX_MODEL", raising=False)
    monkeypatch.delenv("AUTOCEDAR_MODEL", raising=False)
    monkeypatch.delenv("AUTOCEDAR_AUTHOR_MODEL", raising=False)
    monkeypatch.delenv("AUTOCEDAR_CHAT_MODEL", raising=False)
    monkeypatch.setenv("AUTOCEDAR_CONFIG_DIR", str(tmp_path / "config"))
    # Inject a stub client so we don't actually hit anthropic.Anthropic().
    fake = _FakeAnthropic(_make_response(SchemaAtomsResponse(atoms=[])))
    client = LLMClient(client=fake)
    assert DEFAULT_MODEL == DEFAULT_CODEX_MODEL
    assert client._provider == "codex"
    assert client._model == DEFAULT_CODEX_MODEL


def test_anthropic_provider_uses_anthropic_default_when_explicit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _FakeAnthropic(_make_response(SchemaAtomsResponse(atoms=[])))
    monkeypatch.setenv("AUTOCEDAR_PROVIDER", "anthropic")
    monkeypatch.delenv("AUTOCEDAR_MODEL", raising=False)
    monkeypatch.delenv("AUTOCEDAR_AUTHOR_MODEL", raising=False)
    monkeypatch.delenv("AUTOCEDAR_CHAT_MODEL", raising=False)

    client = LLMClient(client=fake)

    assert client._provider == "anthropic"
    assert client._model == DEFAULT_ANTHROPIC_MODEL


def test_construction_with_custom_model() -> None:
    fake = _FakeAnthropic(_make_response(SchemaAtomsResponse(atoms=[])))
    client = LLMClient(client=fake, model="claude-sonnet-4-6")
    assert client._model == "claude-sonnet-4-6"


def test_default_effort_is_high() -> None:
    fake = _FakeAnthropic(_make_response(SchemaAtomsResponse(atoms=[])))
    client = LLMClient(client=fake)
    assert client._effort == DEFAULT_EFFORT == "high"


def test_omitted_effort_uses_resolved_provider_setting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _FakeAnthropic(_make_response(SchemaAtomsResponse(atoms=[])))
    monkeypatch.setenv("AUTOCEDAR_EFFORT", "medium")

    client = LLMClient(client=fake)

    assert client._effort == "medium"


def test_codex_provider_uses_codex_default_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AUTOCEDAR_PROVIDER", "codex")
    monkeypatch.setenv("AUTOCEDAR_CODEX_MODEL", "gpt-test")

    client = LLMClient(backend=object())  # type: ignore[arg-type]

    assert client._provider == "codex"
    assert client._model == "gpt-test"


def test_openai_provider_is_direct_api_not_codex_alias(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AUTOCEDAR_PROVIDER", "openai")
    monkeypatch.setenv("AUTOCEDAR_OPENAI_MODEL", "gpt-api-test")

    client = LLMClient(backend=object())  # type: ignore[arg-type]

    assert client._provider == "openai"
    assert client._model == "gpt-api-test"


def test_openai_compatible_provider_uses_local_client_and_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sentinel = object()
    monkeypatch.setenv("AUTOCEDAR_PROVIDER", "local")
    monkeypatch.setenv("AUTOCEDAR_LOCAL_MODEL", "served-local-model")

    client = LLMClient(backend=sentinel)  # type: ignore[arg-type]

    assert client._client is sentinel
    assert client._provider == "local"
    assert client._model == "served-local-model"


def test_unknown_provider_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AUTOCEDAR_PROVIDER", "mystery")

    with pytest.raises(ValueError, match="Unknown provider"):
        LLMClient()


def test_create_runtime_backend_threads_local_endpoint_and_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = ResolvedProviderConfig(
        provider="local",
        model="served-model",
        base_url="http://node:8000/v1",
        reasoning_effort=None,
        sources={},
    )
    seen: dict[str, Any] = {}
    sentinel = object()
    monkeypatch.setattr(
        "autocedar.llm.resolve_api_key",
        lambda provider, *, session_api_key=None: SimpleNamespace(api_key="local-key"),
    )
    monkeypatch.setattr(
        "autocedar.llm.create_backend",
        lambda provider, **kwargs: seen.update(provider=provider, **kwargs) or sentinel,
    )

    assert create_runtime_backend(config) is sentinel
    assert seen == {
        "provider": "local",
        "base_url": "http://node:8000/v1",
        "api_key": "local-key",
    }


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


def test_schema_atomization_prompt_requires_lifecycle_state_to_be_representable() -> None:
    fake = _FakeAnthropic(_make_response(SchemaAtomsResponse(atoms=[])))
    client = LLMClient(client=fake)
    client.propose_schema_atoms(
        "Students cannot register for course offerings after registration is closed.",
    )

    kwargs = fake.messages.last_kwargs
    system_text = "\n".join(block["text"] for block in kwargs["system"])
    assert "lifecycle state" in system_text
    assert "registration open/closed" in system_text
    assert "connect" in system_text


def test_schema_atomization_prompt_requires_request_environment_context() -> None:
    fake = _FakeAnthropic(_make_response(SchemaAtomsResponse(atoms=[])))
    client = LLMClient(client=fake)
    client.propose_schema_atoms(
        "Students register for courses from personal computers attached to the campus LAN.",
    )

    kwargs = fake.messages.last_kwargs
    system_text = "\n".join(block["text"] for block in kwargs["system"])
    assert "request environment" in system_text
    assert "from campus LAN" in system_text
    assert "addCourseOffering" in system_text
    assert "request-context fields" in system_text


def test_schema_atomization_prompt_requires_no_conflict_context() -> None:
    fake = _FakeAnthropic(_make_response(SchemaAtomsResponse(atoms=[])))
    client = LLMClient(client=fake)
    client.propose_schema_atoms(
        "A professor may select a course offering if there is no conflict.",
    )

    kwargs = fake.messages.last_kwargs
    system_text = "\n".join(block["text"] for block in kwargs["system"])
    assert "no conflict" in system_text
    assert "hasScheduleConflict" in system_text
    assert "unassigned" in system_text


def test_schema_atomization_prompt_requires_owned_target_identity() -> None:
    fake = _FakeAnthropic(_make_response(SchemaAtomsResponse(atoms=[])))
    client = LLMClient(client=fake)
    client.propose_schema_atoms(
        "The system must prevent students from changing schedules other than their own.",
    )

    kwargs = fake.messages.last_kwargs
    system_text = "\n".join(block["text"] for block in kwargs["system"])
    assert "their own" in system_text
    assert "owner/target identity" in system_text
    assert "context.student: Student" in system_text
    assert "principal ==" in system_text
    assert "context.student" in system_text
    assert "action name alone" in system_text


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
# propose_property_atom — Stage 2 one-atom protocol with mocked LLM.
# ---------------------------------------------------------------------------


def test_propose_property_atom_returns_translated_dataclass() -> None:
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
                    required_schema_support=[
                        _LLMRequiredSchemaSupport(
                            kind="attribute",
                            entity="Resource",
                            field_name="owner",
                            reason="The Cedar reference compares principal to resource.owner.",
                        ),
                    ],
                ),
            ],
        ),
    )
    fake = _FakeAnthropic(fake_response)
    client = LLMClient(client=fake)
    atom = client.propose_property_atom(
        "Owners can read.",
        "entity User;",
        prior_atoms=[],
        prior_decisions=[],
    )

    assert isinstance(atom, PropertyAtom)
    assert atom.constraint_type == "ceiling"
    assert atom.action == "read"
    assert atom.required_schema_support[0].kind == "attribute"
    assert atom.required_schema_support[0].entity == "Resource"
    assert atom.required_schema_support[0].field_name == "owner"


def test_propose_property_atom_includes_schema_and_one_atom_contract() -> None:
    fake = _FakeAnthropic(_make_response(PropertyAtomsResponse(atoms=[])))
    client = LLMClient(client=fake)
    prior = PropertyAtom(
        name="owner_must_read",
        rationale="required permission",
        plain_english_summary="Owners must read.",
        source_excerpt="Owners can read.",
        constraint_type="floor",
        action="read",
        principal_types=["User"],
        resource_types=["Resource"],
        reference_cedar='permit (principal, action == Action::"read", resource);',
    )
    prior_decision = SimpleNamespace(
        atom_name="bad_atom",
        action="reject",
        reason="not in the spec",
        edit_delta={},
    )
    client.propose_property_atom(
        "Owners can read.",
        "entity User;",
        prior_atoms=[prior],
        prior_decisions=[prior_decision],
    )

    kwargs = fake.messages.last_kwargs
    assert kwargs["output_format"] is PropertyAtomsResponse
    user_turn = kwargs["messages"][0]["content"]
    assert "```cedarschema\nentity User;\n```" in user_turn
    assert "Propose exactly ONE next Stage 2 property atom" in user_turn
    assert "The property atom is the review unit" in user_turn
    assert "Coverage instruction for this next atom" in user_turn
    assert "No approved floor atoms exist yet" not in user_turn
    assert "owner_must_read" in user_turn
    assert "bad_atom" in user_turn


def test_property_atom_prompt_prioritizes_floor_when_none_approved() -> None:
    fake = _FakeAnthropic(_make_response(PropertyAtomsResponse(atoms=[])))
    client = LLMClient(client=fake)

    client.propose_property_atom(
        "Students can register for courses.",
        "entity Student;",
        prior_atoms=[],
        prior_decisions=[],
    )

    user_turn = fake.messages.last_kwargs["messages"][0]["content"]
    assert "No approved floor atoms exist yet" in user_turn
    assert "propose one missing floor atom now" in user_turn


def test_property_coverage_instruction_prioritizes_floor_with_only_safety() -> None:
    safety = PropertyAtom(
        name="owner_only_read",
        rationale="safety",
        plain_english_summary="Only owners read.",
        source_excerpt="Only owners can read.",
        constraint_type="ceiling",
        action="read",
        principal_types=["User"],
        resource_types=["Resource"],
        reference_cedar='permit (principal, action == Action::"read", resource);',
    )

    instruction = _property_coverage_instruction([safety])

    assert "No approved floor atoms exist yet" in instruction
    assert "propose one missing floor atom now" in instruction


def test_property_coverage_instruction_balances_safety_after_some_floors() -> None:
    floor = PropertyAtom(
        name="owner_must_read",
        rationale="floor",
        plain_english_summary="Owners must read.",
        source_excerpt="Owners can read.",
        constraint_type="floor",
        action="read",
        principal_types=["User"],
        resource_types=["Resource"],
        reference_cedar='permit (principal, action == Action::"read", resource);',
    )
    safety_atoms = [
        PropertyAtom(
            name=f"safety_{i}",
            rationale="safety",
            plain_english_summary="Safety.",
            source_excerpt="Only owners can read.",
            constraint_type="ceiling",
            action="read",
            principal_types=["User"],
            resource_types=["Resource"],
            reference_cedar='permit (principal, action == Action::"read", resource);',
        )
        for i in range(3)
    ]

    instruction = _property_coverage_instruction([floor, *safety_atoms])

    assert "Safety atoms currently outnumber floors" in instruction
    assert "Prefer the next missing floor" in instruction


def test_property_coverage_instruction_audits_scoped_floors_before_stopping() -> None:
    floor = PropertyAtom(
        name="professor_select_floor",
        rationale="positive workflow",
        plain_english_summary="Professor may select an eligible offering when there is no conflict.",
        source_excerpt="If there is no conflict...",
        constraint_type="floor",
        action="selectCourseOfferingToTeach",
        principal_types=["Professor"],
        resource_types=["CourseOffering"],
        reference_cedar=(
            'permit (principal, action == Action::"selectCourseOfferingToTeach", resource) '
            "when { principal.eligibleCourses.contains(resource.course) && !context.hasScheduleConflict };"
        ),
    )
    ceiling = PropertyAtom(
        name="some_other_ceiling",
        rationale="safety",
        plain_english_summary="Some other safety condition.",
        source_excerpt="cannot...",
        constraint_type="ceiling",
        action="selectCourseOfferingToTeach",
        principal_types=["Professor"],
        resource_types=["CourseOffering"],
        reference_cedar='permit (principal, action == Action::"selectCourseOfferingToTeach", resource);',
    )

    instruction = _property_coverage_instruction([floor, ceiling])

    assert "audit existing floors" in instruction
    assert "eligible course" in instruction
    assert "no conflict" in instruction
    assert "upcoming/not-completed semester boundaries" in instruction
    assert "A same-action ceiling for only part of the floor body is not enough" in instruction
    assert "no same-action ceiling/disjointness" in instruction
    assert "bounded allowed slices" in instruction
    assert "team membership" in instruction
    assert "same-action ceiling/disjointness contains that same boundary" in instruction
    assert "union of approved slices" in instruction


def test_property_coverage_instruction_does_not_treat_positive_grants_as_floor_only() -> None:
    floor = PropertyAtom(
        name="doctor_read_care_team_floor",
        rationale="doctor care-team read workflow",
        plain_english_summary="Doctors can read records for patients on their care team.",
        source_excerpt="Doctors can read records for patients on their care team.",
        constraint_type="floor",
        action="readRecord",
        principal_types=["Doctor"],
        resource_types=["Record"],
        reference_cedar=(
            'permit (principal is Doctor, action == Action::"readRecord", resource is Record) '
            "when { resource.careTeam.contains(principal) };"
        ),
    )

    instruction = _property_coverage_instruction([floor])

    assert "Approved floors exist without any same-action ceiling/disjointness" in instruction
    assert "doctor_read_care_team_floor" in instruction
    assert "bounded-grant ceiling/safety side" in instruction
    assert "union of the approved allowed slices" in instruction
    assert "do not emit a narrow ceiling" in instruction


def test_propose_property_atom_returns_none_for_completion() -> None:
    fake = _FakeAnthropic(_make_response(PropertyAtomsResponse(atoms=[])))
    client = LLMClient(client=fake)

    atom = client.propose_property_atom(
        "Owners can read.",
        "entity User;",
        prior_atoms=[],
        prior_decisions=[],
    )

    assert atom is None


def test_codex_property_proposal_uses_low_effort() -> None:
    fake = _FakeAnthropic(_make_response(PropertyAtomsResponse(atoms=[])))
    client = LLMClient(client=fake, provider="codex", model="gpt-5.5", effort="high")

    client.propose_property_atom(
        "Owners can read.",
        "entity User;",
        prior_atoms=[],
        prior_decisions=[],
    )

    assert fake.messages.last_kwargs["output_config"]["effort"] == "low"


def test_disjointness_translation_canonicalizes_forbid_reference() -> None:
    atom = _translate_property_atom(
        _LLMPropertyAtom(
            name="closed_registration_disjointness",
            rationale="registration is closed",
            plain_english_summary="Students cannot register after registration closes.",
            source_excerpt="Students cannot register ... after registration ... has been closed.",
            constraint_type="disjointness",
            action="registerForCourseOffering",
            principal_types=["Student"],
            resource_types=["CourseOffering"],
            reference_cedar=(
                'forbid (principal, action == Action::"registerForCourseOffering", resource) '
                "when { resource.semester.isCurrent && !resource.registrationPeriod.isOpen };"
            ),
            disjoint_with="closed_registration",
            disjoint_target_body="resource.semester.isCurrent && !resource.registrationPeriod.isOpen",
        ),
    )

    assert atom.reference_cedar.startswith("permit (principal is Student")
    assert 'action == Action::"registerForCourseOffering"' in atom.reference_cedar
    assert "resource is CourseOffering" in atom.reference_cedar
    assert "!(resource.semester.isCurrent && !resource.registrationPeriod.isOpen)" in atom.reference_cedar


def test_disjointness_translation_infers_missing_disjoint_with_label() -> None:
    atom = _translate_property_atom(
        _LLMPropertyAtom(
            name="tas_must_not_assign_external_grades",
            rationale="TA external-grade assignment is forbidden.",
            plain_english_summary="Teaching assistants must not assign external grades.",
            source_excerpt="TA can view and assign InternalGrades but not ExternalGrades.",
            constraint_type="disjointness",
            action="assignExternalGrade",
            principal_types=["User"],
            resource_types=["ExternalGrade"],
            reference_cedar="",
            disjoint_target_body='principal in TeachingAssistant::"TeachingAssistant"',
        ),
    )

    assert atom.disjoint_with == "tas_must_not_assign_external_grades_target"
    assert atom.disjoint_target_body == 'principal in TeachingAssistant::"TeachingAssistant"'
    assert "!(principal in TeachingAssistant::\"TeachingAssistant\")" in atom.reference_cedar


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

    client.propose_property_atom(spec, schema, prior_atoms=[], prior_decisions=[])

    kwargs = fake.messages.last_kwargs
    system_text = "\n".join(block["text"] for block in kwargs["system"])
    assert "Prefer `disjointness` for explicit deny/override language" in system_text
    assert "closed tickets cannot be commented on" in system_text
    assert "not a `forbid` policy" in system_text
    assert 'permit (...) when { !(resource.status == "closed") };' in system_text
    assert "Do not emit duplicate liveness atoms" in system_text
    assert spec in system_text
    assert f"```cedarschema\n{schema}\n```" in kwargs["messages"][0]["content"]


def test_property_atomization_prompt_covers_closed_periods_and_negated_has_trap() -> None:
    fake = _FakeAnthropic(_make_response(PropertyAtomsResponse(atoms=[])))
    client = LLMClient(client=fake)
    spec = (
        "Students cannot register for course offerings after registration is closed. "
        "Professors cannot change course offerings after registration is closed."
    )
    schema = (
        "entity RegistrationPeriod { isOpen: Bool, };\n"
        "entity CourseOffering { registration: RegistrationPeriod, instructor?: Professor, };\n"
        "entity Student;\n"
        "entity Professor;\n"
    )

    client.propose_property_atom(spec, schema, prior_atoms=[], prior_decisions=[])

    kwargs = fake.messages.last_kwargs
    system_text = "\n".join(block["text"] for block in kwargs["system"])
    normalized_system_text = " ".join(system_text.split())
    assert "!(x has field) || (x has field && x.field == value)" in system_text
    assert "Cover every explicit safety sentence" in system_text
    assert "after X is closed" in system_text
    assert "registration is closed" in system_text
    assert "For mutable actions" in system_text
    assert "broad floor" in normalized_system_text
    assert "open registration" in normalized_system_text
    assert "eligible/no-conflict/upcoming" in normalized_system_text
    assert "not a completed semester" in normalized_system_text
    assert "for the upcoming semester" in normalized_system_text
    assert "A same-action ceiling only covers the floor boundary" in system_text
    assert "eligible && noConflict && upcoming && notCompleted" in system_text
    assert "Ceilings are not optional when the prose names necessary conditions" in system_text
    assert "Before returning an empty `atoms` list" in system_text
    assert "Positive conditional permissions are usually bounded grants" in system_text
    assert "Doctors can read records for patients on their care team" in normalized_system_text
    assert "floor-only" in system_text
    assert "reviewer should eventually see both sides of the grant" in system_text
    assert "Primitive same-action ceilings compose as intersections" in system_text
    assert "union of all approved slices" in system_text
    assert "floor-only only" in system_text
    assert "if it only gives a sufficient condition, use a floor" not in system_text


def test_property_atomization_prompt_requires_action_context_conditions() -> None:
    fake = _FakeAnthropic(_make_response(PropertyAtomsResponse(atoms=[])))
    client = LLMClient(client=fake)
    client.propose_property_atom(
        "Students register from campus LAN and professors record grades with extra security.",
        "entity Student; entity Professor;",
        prior_atoms=[],
        prior_decisions=[],
    )

    kwargs = fake.messages.last_kwargs
    system_text = "\n".join(block["text"] for block in kwargs["system"])
    assert "action has request context fields" in system_text
    assert "Floors are not optional" in system_text
    assert "context.fromCampusLan" in system_text
    assert "context.strongAuthentication" in system_text
    assert "context.hasScheduleConflict" in system_text
    assert "context.student" in system_text
    assert "context.grade" in system_text


def test_property_atomization_prompt_requires_owned_target_equality() -> None:
    fake = _FakeAnthropic(_make_response(PropertyAtomsResponse(atoms=[])))
    client = LLMClient(client=fake)
    client.propose_property_atom(
        "Students must not change schedules other than their own.",
        "entity Student;",
        prior_atoms=[],
        prior_decisions=[],
    )

    kwargs = fake.messages.last_kwargs
    system_text = "\n".join(block["text"] for block in kwargs["system"])
    assert "other than their own" in system_text
    assert "principal == resource.owner" in system_text
    assert "resource.student" in system_text
    assert "principal == context.student" in system_text
    assert "principal type alone" in system_text


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
    assert "Preserve the same source requirement, action, principal" in user_turn
    assert "repaired floor" in user_turn
    assert "avoid reusing the name of any already-approved atom" in user_turn


def test_propose_property_atom_falls_back_when_grammar_compilation_times_out() -> None:
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

    atom = client.propose_property_atom(
        "Owners can read.",
        "entity User;",
        prior_atoms=[],
        prior_decisions=[],
    )

    assert atom is not None
    assert atom.name == "owner_only_read"
    assert fake.messages.parse_count == 1
    assert fake.messages.create_count == 1
    assert fake.messages.create_kwargs is not None
    assert "The structured-output grammar compiler timed out" in fake.messages.create_kwargs[
        "messages"
    ][-1]["content"]


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
