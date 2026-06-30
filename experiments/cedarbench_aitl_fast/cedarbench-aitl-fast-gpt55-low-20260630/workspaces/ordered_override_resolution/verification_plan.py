"""Hand-authored verification plan for realworld/ordered_override_resolution.

Quota policy where THREE rules have explicit precedence:
  Rule 1 (highest):  per-user customQuota (when present) overrides all
  Rule 2 (medium):   enterprise tier -> unlimited (when no customQuota)
  Rule 3 (lowest):   tier defaults free<10 / pro<100 (when neither above)

Cedar has no native rule priorities; precedence is encoded via
guards on the lower-priority branches negating the
higher-priority conditions.

Floors test each precedence branch firing under its proper guard:
  - floor_custom_quota_overrides_tier:  Rule 1 wins regardless of tier
  - floor_enterprise_unlimited:         Rule 2 wins when no customQuota
  - floor_free_under_limit:             Rule 3 (free)
  - floor_pro_under_limit:              Rule 3 (pro)
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceiling --------------------------------------------------
        {
            "name": "call_safety",
            "description": (
                "call permitted only when one of: "
                "(1) customQuota present and requestCount < customQuota, "
                "(2) no customQuota and tier == enterprise, "
                "(3) no customQuota and ((tier == free and < 10) "
                "or (tier == pro and < 100))"
            ),
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"call"',
            "resource_type": "Service",
            "reference_path": os.path.join(REFS, "call_safety.cedar"),
        },

        # -- Floors ----------------------------------------------------------
        {
            "name": "floor_custom_quota_overrides_tier",
            "description": (
                "Rule 1 (highest): user with customQuota MUST be "
                "permitted iff requestCount < customQuota -- "
                "regardless of tier"
            ),
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"call"',
            "resource_type": "Service",
            "floor_path": os.path.join(
                REFS, "floor_custom_quota_overrides_tier.cedar"
            ),
        },
        {
            "name": "floor_enterprise_unlimited",
            "description": (
                "Rule 2 (medium): enterprise user with no customQuota "
                "MUST be permitted regardless of requestCount"
            ),
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"call"',
            "resource_type": "Service",
            "floor_path": os.path.join(
                REFS, "floor_enterprise_unlimited.cedar"
            ),
        },
        {
            "name": "floor_free_under_limit",
            "description": (
                "Rule 3 (lowest, free): free-tier user with no "
                "customQuota and requestCount < 10 MUST be permitted"
            ),
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"call"',
            "resource_type": "Service",
            "floor_path": os.path.join(
                REFS, "floor_free_under_limit.cedar"
            ),
        },
        {
            "name": "floor_pro_under_limit",
            "description": (
                "Rule 3 (lowest, pro): pro-tier user with no "
                "customQuota and requestCount < 100 MUST be permitted"
            ),
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"call"',
            "resource_type": "Service",
            "floor_path": os.path.join(
                REFS, "floor_pro_under_limit.cedar"
            ),
        },

        # -- Liveness --------------------------------------------------------
        {
            "name": "liveness_call",
            "description": "User+call+Service liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"call"',
            "resource_type": "Service",
        },
    ]
