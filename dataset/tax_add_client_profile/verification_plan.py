"""Hand-authored verification plan for tax_add_client_profile.

Extends tax_base with a new `viewClientProfile` action targeting Client
resources. The consent forbid on viewDocument does NOT apply to
viewClientProfile (it's action-scoped).

Note on expressibility: the spec requires "exists orgInfo in
principal.assigned_orgs where orgInfo.organization == resource.organization".
Cedar's base `.contains()` requires exact record equality and has no
existential quantifier over set members. The viewClientProfile ceiling
is therefore loose (no condition), and the floor is a simple liveness
requirement — this is documented in the reference file. This is an
acknowledged spec/language expressibility gap, flagged as a harness
improvement target (spec/Cedar compatibility check).
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # ── viewDocument (unchanged from tax_base) ───────────────────────
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

        # ── viewClientProfile (new) ──────────────────────────────────────
        {
            "name": "viewClientProfile_ceiling",
            "description": "Professional may viewClientProfile (loose ceiling — exact org match not expressible in Cedar)",
            "type": "implies",
            "principal_type": "Taxpreparer::Professional",
            "action": "Taxpreparer::Action::\"viewClientProfile\"",
            "resource_type": "Taxpreparer::Client",
            "reference_path": os.path.join(REFS, "viewClientProfile_ceiling.cedar"),
        },

        # ── Liveness ─────────────────────────────────────────────────────
        {
            "name": "liveness_view_document",
            "description": "Professional+viewDocument+Document liveness",
            "type": "always-denies-liveness",
            "principal_type": "Taxpreparer::Professional",
            "action": "Taxpreparer::Action::\"viewDocument\"",
            "resource_type": "Taxpreparer::Document",
        },
        {
            "name": "liveness_view_client_profile",
            "description": "Professional+viewClientProfile+Client liveness",
            "type": "always-denies-liveness",
            "principal_type": "Taxpreparer::Professional",
            "action": "Taxpreparer::Action::\"viewClientProfile\"",
            "resource_type": "Taxpreparer::Client",
        },
    ]
