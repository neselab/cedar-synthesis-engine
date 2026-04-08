"""Hand-authored verification plan for tax_add_supervisor.

Extends tax_base with a Supervisor principal type. Supervisors can view
documents whose owner organization is in their supervised_orgs set
(bypassing Professional's serviceline/location match), subject to the
same consent forbid.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        {"name": "professional_org_match_and_consent_safety", "description": "Professional may viewDocument only when (org match AND valid consent)", "type": "implies", "principal_type": "Taxpreparer::Professional", "action": "Taxpreparer::Action::\"viewDocument\"", "resource_type": "Taxpreparer::Document", "reference_path": os.path.join(REFS, "org_match_and_consent_safety.cedar")},
        {"name": "professional_must_view_org_match_with_consent", "description": "Professional MUST viewDocument when (org match AND valid consent)", "type": "floor", "principal_type": "Taxpreparer::Professional", "action": "Taxpreparer::Action::\"viewDocument\"", "resource_type": "Taxpreparer::Document", "floor_path": os.path.join(REFS, "must_view_org_match_with_consent.cedar")},
        {"name": "supervisor_org_and_consent_safety", "description": "Supervisor may viewDocument only when (supervised org AND valid consent)", "type": "implies", "principal_type": "Taxpreparer::Supervisor", "action": "Taxpreparer::Action::\"viewDocument\"", "resource_type": "Taxpreparer::Document", "reference_path": os.path.join(REFS, "supervisor_org_and_consent_safety.cedar")},
        {"name": "supervisor_must_view_with_consent", "description": "Supervisor MUST viewDocument when (supervised org AND valid consent)", "type": "floor", "principal_type": "Taxpreparer::Supervisor", "action": "Taxpreparer::Action::\"viewDocument\"", "resource_type": "Taxpreparer::Document", "floor_path": os.path.join(REFS, "supervisor_must_view_with_consent.cedar")},
        {"name": "liveness_professional_view", "description": "Professional+viewDocument liveness", "type": "always-denies-liveness", "principal_type": "Taxpreparer::Professional", "action": "Taxpreparer::Action::\"viewDocument\"", "resource_type": "Taxpreparer::Document"},
        {"name": "liveness_supervisor_view", "description": "Supervisor+viewDocument liveness", "type": "always-denies-liveness", "principal_type": "Taxpreparer::Supervisor", "action": "Taxpreparer::Action::\"viewDocument\"", "resource_type": "Taxpreparer::Document"},
    ]
