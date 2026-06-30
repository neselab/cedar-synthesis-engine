"""Hand-authored verification plan for realworld/multi_forbid_floor_consistency.

Stress test for §8.8 (floor-bound consistency) at the 4-way boundary:
every floor must be jointly satisfiable with FOUR distinct global
forbids. A naïve floor that omits any of the four forbid negations will
contradict the corresponding global forbid and fail the implies check
against the ceiling (which only permits when all four forbids are
absent).

Four forbids in scope:
  1. Suspended users blocked (both actions)
  2. Outside business hours blocks `access` (not `view`)
  3. Classified resources require MFA (both actions)
  4. Approval-flagged resources require attestation for `access`
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # ── Safety ceilings ──────────────────────────────────────────────
        {
            "name": "access_safety",
            "description": "access permitted only when none of the four forbid conditions are triggered",
            "type": "implies",
            "principal_type": "User",
            "action": "Action::\"access\"",
            "resource_type": "Resource",
            "reference_path": os.path.join(REFS, "access_safety.cedar"),
        },
        {
            "name": "view_safety",
            "description": "view permitted only when forbids 1 (suspension) and 3 (classified-MFA) are absent",
            "type": "implies",
            "principal_type": "User",
            "action": "Action::\"view\"",
            "resource_type": "Resource",
            "reference_path": os.path.join(REFS, "view_safety.cedar"),
        },

        # ── Floors (access — must satisfy all 4 forbid negations) ───────
        {
            "name": "floor_access_clean",
            "description": "Any non-suspended user MUST access a clean (non-classified, non-approval) resource during business hours",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"access\"",
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "floor_access_clean.cedar"),
        },
        {
            "name": "floor_access_classified_mfa",
            "description": "MFA-verified user MUST access a classified, non-approval resource during business hours",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"access\"",
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "floor_access_classified_mfa.cedar"),
        },
        {
            "name": "floor_access_approval",
            "description": "Any non-suspended user MUST access a non-classified, approval-flagged resource during business hours when approval is attested",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"access\"",
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "floor_access_approval.cedar"),
        },
        {
            "name": "floor_access_both",
            "description": "MFA-verified user MUST access a classified approval-flagged resource during business hours when approval is attested",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"access\"",
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "floor_access_both.cedar"),
        },

        # ── Floors (view — only forbids 1 and 3 apply) ──────────────────
        {
            "name": "floor_view_unclassified",
            "description": "Any non-suspended user MUST view a non-classified resource regardless of hours or approval",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"view\"",
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "floor_view_unclassified.cedar"),
        },
        {
            "name": "floor_view_classified_mfa",
            "description": "MFA-verified non-suspended user MUST view a classified resource regardless of hours or approval",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"view\"",
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "floor_view_classified_mfa.cedar"),
        },

        # ── Liveness ─────────────────────────────────────────────────────
        {
            "name": "liveness_access",
            "description": "User+access+Resource liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": "Action::\"access\"",
            "resource_type": "Resource",
        },
        {
            "name": "liveness_view",
            "description": "User+view+Resource liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": "Action::\"view\"",
            "resource_type": "Resource",
        },
    ]
