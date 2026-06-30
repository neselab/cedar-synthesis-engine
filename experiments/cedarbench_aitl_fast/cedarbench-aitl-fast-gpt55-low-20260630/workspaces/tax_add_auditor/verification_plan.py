"""Hand-authored verification plan for tax_add_auditor.

Extends tax_base with a new Auditor principal type. Auditors can view any
document whose serviceline is in their auditScope (bypassing org matching
that Professionals require), but the consent forbid still applies to them.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # ── Professional checks (same as tax_base) ───────────────────────
        {
            "name": "professional_org_match_and_consent_safety",
            "description": "Professional may viewDocument only when (org match AND valid consent)",
            "type": "implies",
            "principal_type": "Taxpreparer::Professional",
            "action": "Taxpreparer::Action::\"viewDocument\"",
            "resource_type": "Taxpreparer::Document",
            "reference_path": os.path.join(REFS, "org_match_and_consent_safety.cedar"),
        },
        {
            "name": "professional_must_view_org_match_with_consent",
            "description": "Professional MUST viewDocument when (org match AND valid consent)",
            "type": "floor",
            "principal_type": "Taxpreparer::Professional",
            "action": "Taxpreparer::Action::\"viewDocument\"",
            "resource_type": "Taxpreparer::Document",
            "floor_path": os.path.join(REFS, "must_view_org_match_with_consent.cedar"),
        },

        # ── Auditor checks ───────────────────────────────────────────────
        {
            "name": "auditor_scope_and_consent_safety",
            "description": "Auditor may viewDocument only when (serviceline in auditScope AND valid consent)",
            "type": "implies",
            "principal_type": "Taxpreparer::Auditor",
            "action": "Taxpreparer::Action::\"viewDocument\"",
            "resource_type": "Taxpreparer::Document",
            "reference_path": os.path.join(REFS, "auditor_scope_and_consent_safety.cedar"),
        },
        {
            "name": "auditor_must_view_scope_with_consent",
            "description": "Auditor MUST viewDocument when (serviceline in auditScope AND valid consent)",
            "type": "floor",
            "principal_type": "Taxpreparer::Auditor",
            "action": "Taxpreparer::Action::\"viewDocument\"",
            "resource_type": "Taxpreparer::Document",
            "floor_path": os.path.join(REFS, "auditor_must_view_scope_with_consent.cedar"),
        },

        # ── Liveness ─────────────────────────────────────────────────────
        {
            "name": "liveness_professional_view",
            "description": "Professional+viewDocument+Document liveness",
            "type": "always-denies-liveness",
            "principal_type": "Taxpreparer::Professional",
            "action": "Taxpreparer::Action::\"viewDocument\"",
            "resource_type": "Taxpreparer::Document",
        },
        {
            "name": "liveness_auditor_view",
            "description": "Auditor+viewDocument+Document liveness",
            "type": "always-denies-liveness",
            "principal_type": "Taxpreparer::Auditor",
            "action": "Taxpreparer::Action::\"viewDocument\"",
            "resource_type": "Taxpreparer::Document",
        },
    ]
