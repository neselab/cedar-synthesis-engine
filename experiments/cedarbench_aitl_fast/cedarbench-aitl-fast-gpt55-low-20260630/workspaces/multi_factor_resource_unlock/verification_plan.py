"""Hand-authored verification plan for realworld/multi_factor_resource_unlock.

Graduated multi-factor unlock for a secrets vault. Tests:
  - Multiple boolean context attestations (hasMfa, hasManagerApproval,
    hasSecurityReview) that combine differently per action and level.
  - Role-gated actions (rotate = security_officer/admin, revoke = admin)
    composed with context factor requirements.
  - Graduated unlock levels: higher sensitivityLevel demands more factors,
    so a uniform-factor candidate fails either ceilings or floors.

Hunts for the failure mode where the model applies the same factor set
uniformly to all sensitivity levels, or omits the role restriction on
rotate/revoke.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceilings (one per action) --------------------------------
        {
            "name": "view_safety",
            "description": (
                "view permitted only when correct factors present for "
                "sensitivity level (L1: none, L2: MFA, L3: MFA+approval)"
            ),
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"view"',
            "resource_type": "Secret",
            "reference_path": os.path.join(REFS, "view_safety.cedar"),
        },
        {
            "name": "rotate_safety",
            "description": (
                "rotate permitted only when (security_officer/admin AND "
                "MFA AND (level!=3 OR securityReview))"
            ),
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"rotate"',
            "resource_type": "Secret",
            "reference_path": os.path.join(REFS, "rotate_safety.cedar"),
        },
        {
            "name": "revoke_safety",
            "description": (
                "revoke permitted only when (admin AND MFA AND "
                "managerApproval)"
            ),
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"revoke"',
            "resource_type": "Secret",
            "reference_path": os.path.join(REFS, "revoke_safety.cedar"),
        },

        # -- Floors -----------------------------------------------------------
        {
            "name": "view_level1_must_permit",
            "description": (
                "Any user MUST view a level-1 secret with no factors"
            ),
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"view"',
            "resource_type": "Secret",
            "floor_path": os.path.join(REFS, "view_level1_must_permit.cedar"),
        },
        {
            "name": "view_level3_must_permit",
            "description": (
                "Any user with MFA + managerApproval MUST view a "
                "level-3 secret"
            ),
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"view"',
            "resource_type": "Secret",
            "floor_path": os.path.join(REFS, "view_level3_must_permit.cedar"),
        },
        {
            "name": "rotate_level2_must_permit",
            "description": (
                "Security officer with MFA MUST rotate a level-2 secret"
            ),
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"rotate"',
            "resource_type": "Secret",
            "floor_path": os.path.join(
                REFS, "rotate_level2_must_permit.cedar"
            ),
        },
        {
            "name": "revoke_must_permit",
            "description": (
                "Admin with MFA + managerApproval MUST revoke any secret"
            ),
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"revoke"',
            "resource_type": "Secret",
            "floor_path": os.path.join(REFS, "revoke_must_permit.cedar"),
        },

        # -- Liveness ---------------------------------------------------------
        {
            "name": "liveness_view",
            "description": "User+view+Secret liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"view"',
            "resource_type": "Secret",
        },
        {
            "name": "liveness_rotate",
            "description": "User+rotate+Secret liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"rotate"',
            "resource_type": "Secret",
        },
        {
            "name": "liveness_revoke",
            "description": "User+revoke+Secret liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"revoke"',
            "resource_type": "Secret",
        },
    ]
