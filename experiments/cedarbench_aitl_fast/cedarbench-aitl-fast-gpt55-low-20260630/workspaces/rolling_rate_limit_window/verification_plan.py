"""Hand-authored verification plan for realworld/rolling_rate_limit_window.

API gateway with rolling-window rate limits supplied via context, plus
cost-multiplier-adjusted budgets for the bulk action. Tests:
  - Dual-window numeric comparison (per-minute AND per-hour)
  - Tier-derived thresholds via string matching on tier
  - Context-supplied rolling-window counters
  - Cost-multiplier-adjusted bulk budgets with explicit bound guards
    (so the multiplication cannot overflow Long range)
  - Window-freshness kill-switch (windowExpired)
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceilings (one per action) --------------------------------
        {
            "name": "call_safety",
            "description": (
                "call permitted only when !windowExpired AND one of: "
                "(free + min<60 + hour<1000), "
                "(pro + min<600 + hour<10000), "
                "(enterprise)"
            ),
            "type": "implies",
            "principal_type": "Client",
            "action": 'Action::"call"',
            "resource_type": "Endpoint",
            "reference_path": os.path.join(REFS, "call_safety.cedar"),
        },
        {
            "name": "bulkcall_safety",
            "description": (
                "bulkCall permitted only when !windowExpired AND "
                "1<=costMultiplier<=100 AND "
                "0<=requestsLastMinute<=1000000 AND tier-specific "
                "cost-adjusted budget (free<=100, pro<=1000, "
                "enterprise unlimited)"
            ),
            "type": "implies",
            "principal_type": "Client",
            "action": 'Action::"bulkCall"',
            "resource_type": "Endpoint",
            "reference_path": os.path.join(REFS, "bulkcall_safety.cedar"),
        },

        # -- Floors -----------------------------------------------------------
        {
            "name": "floor_free_call",
            "description": (
                "Free-tier client MUST call when !windowExpired AND "
                "requestsLastMinute<60 AND requestsLastHour<1000"
            ),
            "type": "floor",
            "principal_type": "Client",
            "action": 'Action::"call"',
            "resource_type": "Endpoint",
            "floor_path": os.path.join(REFS, "floor_free_call.cedar"),
        },
        {
            "name": "floor_pro_call",
            "description": (
                "Pro-tier client MUST call when !windowExpired AND "
                "requestsLastMinute<600 AND requestsLastHour<10000"
            ),
            "type": "floor",
            "principal_type": "Client",
            "action": 'Action::"call"',
            "resource_type": "Endpoint",
            "floor_path": os.path.join(REFS, "floor_pro_call.cedar"),
        },
        {
            "name": "floor_enterprise_call",
            "description": (
                "Enterprise-tier client MUST call any endpoint when "
                "!windowExpired (no rate cap)"
            ),
            "type": "floor",
            "principal_type": "Client",
            "action": 'Action::"call"',
            "resource_type": "Endpoint",
            "floor_path": os.path.join(REFS, "floor_enterprise_call.cedar"),
        },
        {
            "name": "floor_pro_bulkcall",
            "description": (
                "Pro-tier client MUST bulkCall when !windowExpired, "
                "costMultiplier in 1..100, requestsLastMinute in "
                "0..1000000, AND requestsLastMinute*costMultiplier<=1000"
            ),
            "type": "floor",
            "principal_type": "Client",
            "action": 'Action::"bulkCall"',
            "resource_type": "Endpoint",
            "floor_path": os.path.join(REFS, "floor_pro_bulkcall.cedar"),
        },

        # -- Liveness ---------------------------------------------------------
        {
            "name": "liveness_call",
            "description": "Client+call+Endpoint liveness",
            "type": "always-denies-liveness",
            "principal_type": "Client",
            "action": 'Action::"call"',
            "resource_type": "Endpoint",
        },
        {
            "name": "liveness_bulkcall",
            "description": "Client+bulkCall+Endpoint liveness",
            "type": "always-denies-liveness",
            "principal_type": "Client",
            "action": 'Action::"bulkCall"',
            "resource_type": "Endpoint",
        },
    ]
