from __future__ import annotations

import textwrap

from autocedar.atoms import PropertyAtom
from autocedar.identity_model import find_identity_issues


SCHEMA = textwrap.dedent(
    """\
    entity User;

    entity Patient in [User] {
        user: User,
        personalRepresentatives: Set<User>,
    };

    entity LicensedHealthCareProfessional in [User] {
        user: User,
    };

    entity Session {
        user: User,
        licensedHealthCareProfessional?: LicensedHealthCareProfessional,
    };

    entity DemographicInformation {
        patient: Patient,
    };

    entity Message {
        sender: User,
        patient?: Patient,
        lhcpRecipient?: LicensedHealthCareProfessional,
    };

    action editDemographicInformation appliesTo {
        principal: [User],
        resource: [DemographicInformation],
        context: {
            session: Session,
        },
    };

    action sendMessage appliesTo {
        principal: [User, LicensedHealthCareProfessional],
        resource: [Message],
        context: {
            session: Session,
            patient: Patient,
        },
    };
    """
)


def _atom(reference_cedar: str, *, action: str = "editDemographicInformation") -> PropertyAtom:
    return PropertyAtom(
        name="identity_test",
        rationale="test",
        plain_english_summary="test",
        source_excerpt="test",
        constraint_type="floor",
        action=action,
        principal_types=["User"],
        resource_types=["DemographicInformation" if action == "editDemographicInformation" else "Message"],
        reference_cedar=reference_cedar,
    )


def test_flags_user_principal_compared_to_patient_resource_field() -> None:
    atom = _atom(
        'permit (principal is User, action == Action::"editDemographicInformation", resource) '
        "when { principal == resource.patient };",
    )

    issues = find_identity_issues(atom, SCHEMA)

    assert len(issues) == 1
    assert issues[0].path == "resource.patient"
    assert issues[0].path_type == "Patient"
    assert issues[0].principal_types == ("User",)


def test_bridge_field_comparison_is_allowed() -> None:
    atom = _atom(
        'permit (principal is User, action == Action::"editDemographicInformation", resource) '
        "when { principal == resource.patient.user };",
    )

    assert find_identity_issues(atom, SCHEMA) == []


def test_same_role_type_comparison_is_allowed() -> None:
    atom = _atom(
        'permit (principal is Patient, action == Action::"editDemographicInformation", resource) '
        "when { principal == resource.patient };",
    )
    atom.principal_types = ["Patient"]

    assert find_identity_issues(atom, SCHEMA) == []


def test_flags_lhcp_principal_compared_to_user_sender() -> None:
    atom = _atom(
        'permit (principal is LicensedHealthCareProfessional, action == Action::"sendMessage", resource) '
        "when { resource.sender == principal };",
        action="sendMessage",
    )
    atom.principal_types = ["LicensedHealthCareProfessional"]

    issues = find_identity_issues(atom, SCHEMA)

    assert len(issues) == 1
    assert issues[0].path == "resource.sender"
    assert issues[0].path_type == "User"
    assert issues[0].principal_types == ("LicensedHealthCareProfessional",)


def test_context_patient_bridge_comparison_is_allowed() -> None:
    atom = _atom(
        'permit (principal is User, action == Action::"sendMessage", resource) '
        "when { principal == context.patient.user };",
        action="sendMessage",
    )

    assert find_identity_issues(atom, SCHEMA) == []
