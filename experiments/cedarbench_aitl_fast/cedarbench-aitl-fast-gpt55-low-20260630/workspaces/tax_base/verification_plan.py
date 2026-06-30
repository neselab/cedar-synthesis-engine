"""Hand-authored verification plan for tax_base.

The tax_base scenario has a single action (viewDocument) with two
conditions that must BOTH hold for permission:
  (a) org match: the professional has an assigned_orgs record whose
      organization / serviceline / location matches the document;
  (b) valid consent: the request's consent names the document's owner
      AND lists the professional's location in its team_region_list.

Entity types are qualified with the Taxpreparer namespace. The base
policy has no ad-hoc template-linked permits (those are added
separately via the host application).
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        {
            "name": "org_match_and_consent_safety",
            "description": "Professional may viewDocument only when (org match AND valid consent)",
            "type": "implies",
            "principal_type": "Taxpreparer::Professional",
            "action": "Taxpreparer::Action::\"viewDocument\"",
            "resource_type": "Taxpreparer::Document",
            "reference_path": os.path.join(REFS, "org_match_and_consent_safety.cedar"),
        },
        {
            "name": "must_view_org_match_with_consent",
            "description": "Professional MUST be permitted to viewDocument when (org match AND valid consent)",
            "type": "floor",
            "principal_type": "Taxpreparer::Professional",
            "action": "Taxpreparer::Action::\"viewDocument\"",
            "resource_type": "Taxpreparer::Document",
            "floor_path": os.path.join(REFS, "must_view_org_match_with_consent.cedar"),
        },
        {
            "name": "liveness_view_document",
            "description": "Professional+viewDocument+Document has at least one permitted request",
            "type": "always-denies-liveness",
            "principal_type": "Taxpreparer::Professional",
            "action": "Taxpreparer::Action::\"viewDocument\"",
            "resource_type": "Taxpreparer::Document",
        },
    ]
