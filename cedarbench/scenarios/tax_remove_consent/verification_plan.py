"""Hand-authored verification plan for tax_remove_consent.

Strips the consent forbid from tax_base. Org matching alone suffices.
The Consent type remains in the schema (context requirement) but the
policy does not enforce it.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        {"name": "org_match_safety", "description": "Professional may viewDocument only when org match holds", "type": "implies", "principal_type": "Taxpreparer::Professional", "action": "Taxpreparer::Action::\"viewDocument\"", "resource_type": "Taxpreparer::Document", "reference_path": os.path.join(REFS, "org_match_safety.cedar")},
        {"name": "must_view_on_org_match", "description": "Professional MUST viewDocument when org match holds", "type": "floor", "principal_type": "Taxpreparer::Professional", "action": "Taxpreparer::Action::\"viewDocument\"", "resource_type": "Taxpreparer::Document", "floor_path": os.path.join(REFS, "must_view_on_org_match.cedar")},
        {"name": "liveness_view_document", "description": "Professional+viewDocument+Document liveness", "type": "always-denies-liveness", "principal_type": "Taxpreparer::Professional", "action": "Taxpreparer::Action::\"viewDocument\"", "resource_type": "Taxpreparer::Document"},
    ]
