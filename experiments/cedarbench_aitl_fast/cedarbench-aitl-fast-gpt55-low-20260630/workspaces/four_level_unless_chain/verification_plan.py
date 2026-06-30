"""Hand-authored verification plan for realworld/four_level_unless_chain.

Encodes a 4-deep nested "unless A unless B unless C unless D" override
chain for emergency-lockdown access. Cedar only has a single `unless`
clause per policy, so the four-level English statement must be flattened
into pure boolean logic — the natural ternary / if-then-else encoding
(§8.11) is not supported.

Hunts for the failure modes:
  - Emitting Cedar ternary syntax (`cond ? a : b`) for the nested chain.
  - Treating `redCellLockdown` as just another disjunct in the `when`
    clause instead of a hard `unless` exclusion that only `hasOverride`
    bypasses.
  - Forgetting that `commanderOverrideActive` re-permits even when
    `lockoutActive` is set.
  - Writing floors that conflict with the redCellLockdown unless (§8.8).
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceilings (one per action) --------------------------------
        {
            "name": "access_safety",
            "description": (
                "access permitted only when the four-level unless chain "
                "resolves to permit: (no lockout OR (emergency+auth) OR "
                "(commander+override window)) AND NOT (redCellLockdown "
                "AND NOT hasOverride)"
            ),
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"access"',
            "resource_type": "Resource",
            "reference_path": os.path.join(REFS, "access_safety.cedar"),
        },
        {
            "name": "forceAccess_safety",
            "description": (
                "forceAccess permitted only for commander with hasOverride; "
                "all four context flags are irrelevant"
            ),
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"forceAccess"',
            "resource_type": "Resource",
            "reference_path": os.path.join(REFS, "forceAccess_safety.cedar"),
        },

        # -- Floors (one per unless level + one for forceAccess) -------------
        {
            "name": "floor_normal_no_lockout",
            "description": (
                "Level 1 base: with no platform lockout and no red-cell "
                "lockdown, any user MUST access"
            ),
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"access"',
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "floor_normal_no_lockout.cedar"),
        },
        {
            "name": "floor_emergency_authorized",
            "description": (
                "Level 2 re-permit: under emergencyMode a user with "
                "hasEmergencyAuth MUST access (red-cell still wins unless "
                "hasOverride)"
            ),
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"access"',
            "resource_type": "Resource",
            "floor_path": os.path.join(
                REFS, "floor_emergency_authorized.cedar"
            ),
        },
        {
            "name": "floor_commander_override_window",
            "description": (
                "Level 3 re-permit: when commanderOverrideActive a "
                "commander MUST access regardless of lockout/emergency"
            ),
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"access"',
            "resource_type": "Resource",
            "floor_path": os.path.join(
                REFS, "floor_commander_override_window.cedar"
            ),
        },
        {
            "name": "floor_red_cell_override_token",
            "description": (
                "Level 4 final bypass: hasOverride must escape the "
                "redCellLockdown hard exclusion (when no platform lockout)"
            ),
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"access"',
            "resource_type": "Resource",
            "floor_path": os.path.join(
                REFS, "floor_red_cell_override_token.cedar"
            ),
        },
        {
            "name": "floor_force_access_commander",
            "description": (
                "A commander with hasOverride MUST forceAccess regardless "
                "of any context flags"
            ),
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"forceAccess"',
            "resource_type": "Resource",
            "floor_path": os.path.join(
                REFS, "floor_force_access_commander.cedar"
            ),
        },

        # -- Liveness ---------------------------------------------------------
        {
            "name": "liveness_access",
            "description": "User+access+Resource liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"access"',
            "resource_type": "Resource",
        },
        {
            "name": "liveness_forceAccess",
            "description": "User+forceAccess+Resource liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"forceAccess"',
            "resource_type": "Resource",
        },
    ]
