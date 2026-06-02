"""Unit tests for ``autocedar.atoms``.

See ``docs/HITL_STEP_B_PLAN.md`` §9 acceptance criterion 1.
"""

import json

import pytest

from autocedar.atoms import (
    ActionAtom,
    AlternativeEncoding,
    AttributeAtom,
    EntityAtom,
    Example,
    PropertyAtom,
    SchemaDraft,
    TypeAliasAtom,
    VerificationPlanDraft,
    from_dict,
    to_dict,
)


# ---------------------------------------------------------------------------
# Stage 1 atom construction.
# ---------------------------------------------------------------------------

def test_entity_atom_construction() -> None:
    e = EntityAtom(
        name="User",
        rationale="Principal of every request.",
        plain_english_summary="The principal in every request.",
        source_excerpt="Doctors and nurses can read records.",
    )
    assert e.name == "User"
    assert e.attributes == {}
    assert e.members_of == []
    assert e.enum_values is None


def test_attribute_atom_with_alternatives_considered() -> None:
    a = AttributeAtom(
        name="user_role",
        rationale="single string role per user",
        plain_english_summary="Each user has one role.",
        source_excerpt="...",
        on_entity="User",
        field_name="role",
        cedar_type="String",
        alternatives_considered=["Set<String>", "principal in Group"],
    )
    assert a.optional is False
    assert "Set<String>" in a.alternatives_considered


def test_action_atom_defaults() -> None:
    a = ActionAtom(
        name="read",
        rationale="read action",
        plain_english_summary="read a record",
        source_excerpt="...",
        principal_types=["User"],
        resource_types=["Record"],
    )
    assert a.context_attributes == {}
    assert a.parent_groups == []


def test_type_alias_atom() -> None:
    t = TypeAliasAtom(
        name="Address",
        rationale="reusable address shape",
        plain_english_summary="A street address record.",
        source_excerpt="...",
        cedar_type="{ street: String, zip: String }",
    )
    assert t.cedar_type.startswith("{")


# ---------------------------------------------------------------------------
# Stage 2 PropertyAtom — primitive vs sugar field validation.
# ---------------------------------------------------------------------------

def test_ceiling_atom_construction() -> None:
    p = PropertyAtom(
        name="careTeam_only_read",
        rationale="bound on read",
        plain_english_summary="Care-team members may read.",
        source_excerpt="Doctors and nurses on the patient's care team can read.",
        constraint_type="ceiling",
        action="read",
        principal_types=["User"],
        resource_types=["Record"],
        reference_cedar=(
            'permit(principal is User, action == Action::"read", resource is Record) '
            "when { resource.careTeamMembers.contains(principal) };"
        ),
    )
    assert p.constraint_type == "ceiling"
    assert p.symbolic_verified is False
    assert p.intent_acknowledged_by_user is False


def test_rate_limit_requires_sugar_fields() -> None:
    with pytest.raises(ValueError, match="rate_limit"):
        PropertyAtom(
            name="bulkExport_rl",
            rationale="rate limit",
            plain_english_summary="100/min",
            source_excerpt="...",
            constraint_type="rate_limit",
            action="bulkExport",
            # Missing: rate_limit_window, threshold, counter_attr.
        )


def test_rate_limit_full_construction() -> None:
    p = PropertyAtom(
        name="bulkExport_rl",
        rationale="rate limit",
        plain_english_summary="100/min",
        source_excerpt="...",
        constraint_type="rate_limit",
        action="bulkExport",
        rate_limit_window="1m",
        rate_limit_threshold=100,
        rate_limit_counter_attr="requestsPerMinute",
    )
    assert p.rate_limit_threshold == 100
    assert p.rate_limit_window == "1m"


def test_disjointness_requires_sugar_fields() -> None:
    with pytest.raises(ValueError, match="disjointness"):
        PropertyAtom(
            name="legal_hold_disj",
            rationale="legal hold off-limits",
            plain_english_summary="legal hold",
            source_excerpt="...",
            constraint_type="disjointness",
            action="read",
            # Missing: disjoint_with AND disjoint_target_body.
        )


def test_disjointness_full_construction() -> None:
    p = PropertyAtom(
        name="legal_hold_disj",
        rationale="legal hold off-limits except legal team",
        plain_english_summary="legal hold off-limits",
        source_excerpt="...",
        constraint_type="disjointness",
        action="read",
        disjoint_with="non_legal_legal_hold_path",
        disjoint_target_body=(
            'resource.legalHold && principal.role != "legal"'
        ),
    )
    assert p.disjoint_with == "non_legal_legal_hold_path"
    assert "legalHold" in (p.disjoint_target_body or "")


def test_primitive_atom_rejects_sugar_fields() -> None:
    with pytest.raises(ValueError, match="ceiling"):
        PropertyAtom(
            name="bad",
            rationale="...",
            plain_english_summary="...",
            source_excerpt="...",
            constraint_type="ceiling",
            action="read",
            rate_limit_threshold=100,  # stray sugar field
        )


# ---------------------------------------------------------------------------
# JSON serialization round-trip.
# ---------------------------------------------------------------------------

def test_property_atom_round_trip() -> None:
    p = PropertyAtom(
        name="careTeam_only_read",
        rationale="bound on read",
        plain_english_summary="Care-team members may read.",
        source_excerpt="...",
        constraint_type="ceiling",
        action="read",
        principal_types=["User"],
        resource_types=["Record"],
        reference_cedar="permit ...;",
        examples_adversarial=[
            Example(
                description="Bob (nurse, on careTeam, NOT primary) → read alice's",
                request_dict={"principal": "User::\"Bob\"", "action": "Action::\"read\""},
                decision_under_chosen="permit",
                decisions_under_alternatives={"primary-nurse-only": "deny"},
                diagnostic_for=["primary-nurse-only"],
            ),
        ],
        alternatives_considered=[
            AlternativeEncoding(
                label="primary-nurse-only",
                interpretive_choice="only the primary nurse, not all care team",
                cedar_text="permit ... when { principal == resource.primaryNurse };",
            ),
        ],
    )

    # Round-trip via to_dict / json / from_dict.
    serialized = json.loads(json.dumps(to_dict(p)))
    assert serialized["constraint_type"] == "ceiling"
    assert serialized["examples_adversarial"][0]["decision_under_chosen"] == "permit"

    restored = from_dict(PropertyAtom, serialized)
    assert restored.name == p.name
    assert restored.examples_adversarial[0].decision_under_chosen == "permit"
    assert restored.alternatives_considered[0].label == "primary-nurse-only"


def test_schema_draft_round_trip() -> None:
    draft = SchemaDraft(
        entities={
            "User": EntityAtom(
                name="User",
                rationale="principal",
                plain_english_summary="user",
                source_excerpt="...",
                attributes={
                    "role": AttributeAtom(
                        name="user_role",
                        rationale="single role",
                        plain_english_summary="role",
                        source_excerpt="...",
                        on_entity="User",
                        field_name="role",
                        cedar_type="String",
                    ),
                },
            ),
        },
    )
    serialized = json.loads(json.dumps(to_dict(draft)))
    restored = from_dict(SchemaDraft, serialized)
    assert restored.entities["User"].attributes["role"].cedar_type == "String"


def test_verification_plan_draft_round_trip() -> None:
    plan = VerificationPlanDraft(
        properties=[
            PropertyAtom(
                name="liveness_read",
                rationale="at least one read permitted",
                plain_english_summary="liveness",
                source_excerpt="...",
                constraint_type="liveness",
                action="read",
            ),
        ],
    )
    serialized = json.loads(json.dumps(to_dict(plan)))
    restored = from_dict(VerificationPlanDraft, serialized)
    assert restored.properties[0].constraint_type == "liveness"


# ---------------------------------------------------------------------------
# Symbolic verified / intent-acknowledged are independently mutable (§1.4).
# ---------------------------------------------------------------------------

def test_verification_flags_are_independent() -> None:
    p = PropertyAtom(
        name="x",
        rationale="...",
        plain_english_summary="...",
        source_excerpt="...",
        constraint_type="floor",
        action="read",
    )
    # Default both False.
    assert (p.symbolic_verified, p.intent_acknowledged_by_user) == (False, False)

    # Symbolic verification can succeed without user approval.
    p.symbolic_verified = True
    assert p.intent_acknowledged_by_user is False

    # User approval can be set independently.
    p.intent_acknowledged_by_user = True
    assert p.symbolic_verified is True  # not reset by approval

    # Round-trip preserves both.
    restored = from_dict(PropertyAtom, json.loads(json.dumps(to_dict(p))))
    assert restored.symbolic_verified is True
    assert restored.intent_acknowledged_by_user is True
