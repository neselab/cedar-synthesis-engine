"""Hand-authored verification plan for realworld/rate_limit_by_role.

API gateway rate limiting where the rate ceiling is derived from the
client's tier attribute.  Tests:
  - Numeric comparison (requestsThisMinute < threshold)
  - Role-derived thresholds via string matching on tier
  - Context-provided counters (gateway-injected request count)
  - Tiered endpoint access (public vs non-public)
  - Action-level restriction (bulkCall = premium only)
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceilings (one per action) --------------------------------
        {
            "name": "call_safety",
            "description": (
                "call permitted only when "
                "(free+public+<100) or (standard+<1000) or (premium)"
            ),
            "type": "implies",
            "principal_type": "ApiClient",
            "action": 'Action::"call"',
            "resource_type": "Endpoint",
            "reference_path": os.path.join(REFS, "call_safety.cedar"),
        },
        {
            "name": "bulkcall_safety",
            "description": (
                "bulkCall permitted only when premium and "
                "requestsThisMinute < 500"
            ),
            "type": "implies",
            "principal_type": "ApiClient",
            "action": 'Action::"bulkCall"',
            "resource_type": "Endpoint",
            "reference_path": os.path.join(REFS, "bulkcall_safety.cedar"),
        },

        # -- Floors -----------------------------------------------------------
        {
            "name": "floor_free_public_call",
            "description": (
                "Free-tier client MUST call a public endpoint when "
                "requestsThisMinute < 100"
            ),
            "type": "floor",
            "principal_type": "ApiClient",
            "action": 'Action::"call"',
            "resource_type": "Endpoint",
            "floor_path": os.path.join(REFS, "floor_free_public_call.cedar"),
        },
        {
            "name": "floor_standard_call",
            "description": (
                "Standard-tier client MUST call any endpoint when "
                "requestsThisMinute < 1000"
            ),
            "type": "floor",
            "principal_type": "ApiClient",
            "action": 'Action::"call"',
            "resource_type": "Endpoint",
            "floor_path": os.path.join(REFS, "floor_standard_call.cedar"),
        },
        {
            "name": "floor_premium_call",
            "description": (
                "Premium-tier client MUST call any endpoint with no "
                "rate limit"
            ),
            "type": "floor",
            "principal_type": "ApiClient",
            "action": 'Action::"call"',
            "resource_type": "Endpoint",
            "floor_path": os.path.join(REFS, "floor_premium_call.cedar"),
        },
        {
            "name": "floor_premium_bulkcall",
            "description": (
                "Premium-tier client MUST bulkCall when "
                "requestsThisMinute < 500"
            ),
            "type": "floor",
            "principal_type": "ApiClient",
            "action": 'Action::"bulkCall"',
            "resource_type": "Endpoint",
            "floor_path": os.path.join(REFS, "floor_premium_bulkcall.cedar"),
        },

        # -- Liveness ---------------------------------------------------------
        {
            "name": "liveness_call",
            "description": "ApiClient+call+Endpoint liveness",
            "type": "always-denies-liveness",
            "principal_type": "ApiClient",
            "action": 'Action::"call"',
            "resource_type": "Endpoint",
        },
        {
            "name": "liveness_bulkcall",
            "description": "ApiClient+bulkCall+Endpoint liveness",
            "type": "always-denies-liveness",
            "principal_type": "ApiClient",
            "action": 'Action::"bulkCall"',
            "resource_type": "Endpoint",
        },
    ]
