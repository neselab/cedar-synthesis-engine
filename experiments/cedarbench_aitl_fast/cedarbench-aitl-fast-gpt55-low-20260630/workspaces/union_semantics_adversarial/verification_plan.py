"""Verification plan for realworld/union_semantics_adversarial.

Tests Cedar's permit-union semantics. The naive encoding
`(groupA || groupB) && (alpha || beta)` is INCORRECT — it permits a
groupA-only user to access beta resources via the cross-product.
The correct encoding requires per-(group, category) coupling:
`(groupA && alpha) || (groupB && beta)`.
"""
import os
REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        {
            "name": "access_safety",
            "description": "access permits MUST be coupled per (group, category); no cross-product",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"access"',
            "resource_type": "Resource",
            "reference_path": os.path.join(REFS, "access_safety.cedar"),
        },
        {
            "name": "floor_groupA_alpha",
            "description": "groupA user MUST access alpha resources",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"access"',
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "floor_groupA_alpha.cedar"),
        },
        {
            "name": "floor_groupB_beta",
            "description": "groupB user MUST access beta resources",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"access"',
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "floor_groupB_beta.cedar"),
        },
        {
            "name": "floor_dual_group_alpha",
            "description": "user in BOTH groups MUST still access alpha resources",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"access"',
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "floor_dual_group_alpha.cedar"),
        },
        {
            "name": "liveness_access",
            "description": "at least one access permitted",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"access"',
            "resource_type": "Resource",
        },
    ]
