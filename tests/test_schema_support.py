"""Tests for the schema hooks a property atom declares (``autocedar.schema_support``)."""

from __future__ import annotations

from autocedar.atoms import RequiredSchemaSupport
from autocedar.schema_support import missing_schema_support

SCHEMA = """
entity Group;
entity User in [Group] = {
    role: String,
    "display name"?: String,
};

entity Submission = {
    authors: Set<User>,
    step1Open: Bool,
};

entity Folder {
    owner: User,
};

action submitStep1 appliesTo {
    principal: [User],
    resource: [Submission],
    context: {
        ip: ipaddr,
    },
};
"""


def _missing(*hooks: RequiredSchemaSupport) -> list[str]:
    return [m.detail for m in missing_schema_support(list(hooks), SCHEMA)]


def test_attributes_are_found_in_every_entity_declaration_form() -> None:
    assert _missing(
        RequiredSchemaSupport(kind="attribute", entity="Submission", field_name="authors"),
        RequiredSchemaSupport(kind="attribute", entity="Submission", field_name="step1Open"),
        RequiredSchemaSupport(kind="attribute", entity="User", field_name="role"),
        RequiredSchemaSupport(kind="attribute", entity="User", field_name="display name"),
        RequiredSchemaSupport(kind="attribute", entity="Folder", field_name="owner"),
    ) == []


def test_missing_hooks_are_still_reported() -> None:
    assert _missing(
        RequiredSchemaSupport(kind="attribute", entity="Submission", field_name="reviewOpen"),
        RequiredSchemaSupport(kind="action_principal", action="submitStep1", type_name="Group"),
        RequiredSchemaSupport(kind="context", action="submitStep1", field_name="time"),
    ) == [
        "entity `Submission` lacks attribute `reviewOpen`",
        "action `submitStep1` does not include principal type `Group`",
        "action `submitStep1` lacks context field `time`",
    ]


def test_action_types_and_context_are_found() -> None:
    assert _missing(
        RequiredSchemaSupport(kind="action_principal", action="submitStep1", type_name="User"),
        RequiredSchemaSupport(kind="action_resource", action="submitStep1", type_name="Submission"),
        RequiredSchemaSupport(kind="context", action="submitStep1", field_name="ip"),
    ) == []


def test_hooks_that_name_nothing_are_skipped() -> None:
    assert _missing(
        RequiredSchemaSupport(kind="action_principal", action="submitStep1", type_name=""),
        RequiredSchemaSupport(kind="action_resource", action="submitStep1"),
        RequiredSchemaSupport(kind="attribute", entity="Submission"),
    ) == []
