"""Hand-authored verification plan for tax_add_edit.

Extends tax_base with a new editDocument action. editDocument follows the
same rules as viewDocument (org match + valid consent), so the check set is
just the tax_base set duplicated for the new action.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # viewDocument (same as tax_base)
        {"name": "view_org_match_and_consent_safety", "description": "Professional may viewDocument only when (org match AND valid consent)", "type": "implies", "principal_type": "Taxpreparer::Professional", "action": "Taxpreparer::Action::\"viewDocument\"", "resource_type": "Taxpreparer::Document", "reference_path": os.path.join(REFS, "org_match_and_consent_safety.cedar")},
        {"name": "view_must_org_match_with_consent", "description": "Professional MUST viewDocument when (org match AND valid consent)", "type": "floor", "principal_type": "Taxpreparer::Professional", "action": "Taxpreparer::Action::\"viewDocument\"", "resource_type": "Taxpreparer::Document", "floor_path": os.path.join(REFS, "must_view_org_match_with_consent.cedar")},
        # editDocument (mirror rules)
        {"name": "edit_org_match_and_consent_safety", "description": "Professional may editDocument only when (org match AND valid consent)", "type": "implies", "principal_type": "Taxpreparer::Professional", "action": "Taxpreparer::Action::\"editDocument\"", "resource_type": "Taxpreparer::Document", "reference_path": os.path.join(REFS, "edit_org_match_and_consent_safety.cedar")},
        {"name": "edit_must_org_match_with_consent", "description": "Professional MUST editDocument when (org match AND valid consent)", "type": "floor", "principal_type": "Taxpreparer::Professional", "action": "Taxpreparer::Action::\"editDocument\"", "resource_type": "Taxpreparer::Document", "floor_path": os.path.join(REFS, "edit_must_view_org_match_with_consent.cedar")},
        # Liveness
        {"name": "liveness_view_document", "description": "Professional+viewDocument+Document liveness", "type": "always-denies-liveness", "principal_type": "Taxpreparer::Professional", "action": "Taxpreparer::Action::\"viewDocument\"", "resource_type": "Taxpreparer::Document"},
        {"name": "liveness_edit_document", "description": "Professional+editDocument+Document liveness", "type": "always-denies-liveness", "principal_type": "Taxpreparer::Professional", "action": "Taxpreparer::Action::\"editDocument\"", "resource_type": "Taxpreparer::Document"},
    ]
