"""Hand-authored verification plan for realworld/exception_to_exception_emergency.

Three-tier nested override chain:
  Tier 1 — lockout suspends normal access.
  Tier 2 — break-glass overrides lockout for hasBreakGlass users.
  Tier 3 — security lockdown trumps break-glass; only securityClearance
            users retain access.

The structural invariant is that Tier 3 dominates Tier 2: a
hasBreakGlass user without clearance must NOT punch through a security
lockdown. Encoded via Cedar's `when ... unless` construct in the
reference policies.

§8.8 floor-bound consistency: every floor in this scenario excludes the
`securityLockdownActive && !securityClearance` case explicitly.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # ── Safety ceilings ──────────────────────────────────────────────
        {
            "name": "access_safety",
            "description": "access permitted only via the normal-or-break-glass path AND not blocked by Tier-3 lockdown",
            "type": "implies",
            "principal_type": "User",
            "action": "Action::\"access\"",
            "resource_type": "Resource",
            "reference_path": os.path.join(REFS, "access_safety.cedar"),
        },
        {
            "name": "security_override_safety",
            "description": "securityOverride permitted only for securityClearance holders",
            "type": "implies",
            "principal_type": "User",
            "action": "Action::\"securityOverride\"",
            "resource_type": "Resource",
            "reference_path": os.path.join(REFS, "security_override_safety.cedar"),
        },

        # ── Positive floors ──────────────────────────────────────────────
        {
            "name": "normal_access_must_permit",
            "description": "Any user MUST be permitted to access in normal mode (no lockout, no lockdown denial)",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"access\"",
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "normal_access_must_permit.cedar"),
        },
        {
            "name": "break_glass_must_permit",
            "description": "hasBreakGlass user with breakGlassInvoked during lockout MUST be permitted (Tier 2)",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"access\"",
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "break_glass_must_permit.cedar"),
        },
        {
            "name": "lockdown_clearance_must_permit",
            "description": "securityClearance holder MUST be permitted during a security lockdown (Tier 3 carve-out)",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"access\"",
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "lockdown_clearance_must_permit.cedar"),
        },
        {
            "name": "security_override_clearance_must_permit",
            "description": "securityClearance holder MUST be permitted to invoke securityOverride",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"securityOverride\"",
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "security_override_clearance_must_permit.cedar"),
        },

        # ── Liveness ─────────────────────────────────────────────────────
        {
            "name": "liveness_access",
            "description": "User+access+Resource has at least one permitted request",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": "Action::\"access\"",
            "resource_type": "Resource",
        },
        {
            "name": "liveness_security_override",
            "description": "User+securityOverride+Resource has at least one permitted request",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": "Action::\"securityOverride\"",
            "resource_type": "Resource",
        },
    ]
