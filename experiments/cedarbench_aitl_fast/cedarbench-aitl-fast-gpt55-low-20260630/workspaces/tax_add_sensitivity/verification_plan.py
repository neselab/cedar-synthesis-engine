"""Hand-authored verification plan for tax_add_sensitivity.

Extends tax_base with an isSensitive attribute on Document and a new
forbid: sensitive documents require "HQ" in consent.team_region_list.
Two floors: one for the non-sensitive case, one for the sensitive+HQ case.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        {"name": "org_match_consent_and_sensitivity_safety", "description": "Professional may viewDocument only when (org match AND valid consent AND (!sensitive OR HQ in team_region_list))", "type": "implies", "principal_type": "Taxpreparer::Professional", "action": "Taxpreparer::Action::\"viewDocument\"", "resource_type": "Taxpreparer::Document", "reference_path": os.path.join(REFS, "org_match_consent_and_sensitivity_safety.cedar")},
        {"name": "must_view_non_sensitive_with_consent", "description": "Professional MUST viewDocument for a NON-sensitive doc with org match + valid consent", "type": "floor", "principal_type": "Taxpreparer::Professional", "action": "Taxpreparer::Action::\"viewDocument\"", "resource_type": "Taxpreparer::Document", "floor_path": os.path.join(REFS, "must_view_non_sensitive_with_consent.cedar")},
        {"name": "must_view_sensitive_with_hq_consent", "description": "Professional MUST viewDocument for a SENSITIVE doc when consent team_region_list contains HQ", "type": "floor", "principal_type": "Taxpreparer::Professional", "action": "Taxpreparer::Action::\"viewDocument\"", "resource_type": "Taxpreparer::Document", "floor_path": os.path.join(REFS, "must_view_sensitive_with_hq_consent.cedar")},
        {"name": "liveness_view_document", "description": "Professional+viewDocument+Document liveness", "type": "always-denies-liveness", "principal_type": "Taxpreparer::Professional", "action": "Taxpreparer::Action::\"viewDocument\"", "resource_type": "Taxpreparer::Document"},
    ]
