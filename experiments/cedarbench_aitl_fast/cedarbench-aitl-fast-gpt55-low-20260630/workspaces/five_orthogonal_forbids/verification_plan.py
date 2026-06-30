"""Hand-authored verification plan for realworld/five_orthogonal_forbids.

Defense-in-depth scenario stacking 5 independent deny conditions:
    1. principal.isBlocked
    2. resource.isArchived
    3. resource.requiresMfa && !principal.mfaVerified
    4. context.outsideBusinessHours
    5. context.rateLimited

The ceiling (`access_safety`) negates all five jointly. Every floor MUST
include all five negations to remain jointly satisfiable with the
ceiling (§8.8). Floors exercise four orthogonal "happy paths" through
the MFA gate and user state to ensure the candidate composes ALL gates
conjunctively rather than dropping one or short-circuiting on a single
attribute.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # ── Safety ceiling ─────────────────────────────────────────────────
        {
            "name": "access_safety",
            "description": (
                "access permitted only when not blocked, not archived, "
                "MFA gate satisfied, in business hours, not rate-limited"
            ),
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"access"',
            "resource_type": "Resource",
            "reference_path": os.path.join(REFS, "access_safety.cedar"),
        },

        # ── Floors (4) — each exercises a different happy path ────────────
        {
            "name": "floor_clean_no_mfa_required",
            "description": (
                "non-blocked user, non-archived non-MFA resource, in hours, "
                "not rate-limited MUST be permitted"
            ),
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"access"',
            "resource_type": "Resource",
            "floor_path": os.path.join(
                REFS, "floor_clean_no_mfa_required.cedar"
            ),
        },
        {
            "name": "floor_clean_with_mfa",
            "description": (
                "non-blocked MFA-verified user, non-archived MFA-required "
                "resource, in hours, not rate-limited MUST be permitted"
            ),
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"access"',
            "resource_type": "Resource",
            "floor_path": os.path.join(
                REFS, "floor_clean_with_mfa.cedar"
            ),
        },
        {
            "name": "floor_mfa_verified_optional_resource",
            "description": (
                "MFA-verified user accessing non-MFA-required resource "
                "(otherwise clean) MUST be permitted"
            ),
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"access"',
            "resource_type": "Resource",
            "floor_path": os.path.join(
                REFS, "floor_mfa_verified_optional_resource.cedar"
            ),
        },
        {
            "name": "floor_unverified_user_no_mfa_resource",
            "description": (
                "user without MFA accessing non-MFA-required resource "
                "(otherwise clean) MUST be permitted"
            ),
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"access"',
            "resource_type": "Resource",
            "floor_path": os.path.join(
                REFS, "floor_unverified_user_no_mfa_resource.cedar"
            ),
        },

        # ── Liveness ──────────────────────────────────────────────────────
        {
            "name": "liveness_access",
            "description": "User+access+Resource liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"access"',
            "resource_type": "Resource",
        },
    ]
