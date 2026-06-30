"""Hand-authored verification plan for realworld/union_principal_types.

API gateway action `callApi` with a principal-type union (User | ApiKey |
ServiceAccount). Each principal kind has different attributes, so the
candidate policy must use Cedar's `is`-typed narrowing in `when` clauses
to read kind-specific fields safely.

Checks:
  - 1 combined ceiling: callApi ⇒ disjunction of three legitimate branches.
  - 3 floors (one per principal type), each requiring the corresponding
    principal kind to be permitted under its own condition.
  - 1 liveness check: at least one User+callApi+Resource request must be
    permitted (User branch; the other two branches' liveness is implied
    by their floor satisfaction).
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # ── Safety ceiling (combined disjunction) ────────────────────────
        {
            "name": "call_api_safety",
            "description": (
                "callApi permitted only when (User with mfaVerified) OR "
                "(ApiKey with scopes containing 'api_call') OR "
                "(ServiceAccount with non-empty serviceName)."
            ),
            "type": "implies",
            "principal_type": "User",
            "action": "Action::\"callApi\"",
            "resource_type": "Resource",
            "reference_path": os.path.join(REFS, "call_api_safety.cedar"),
        },

        # ── Floors (one per principal type) ──────────────────────────────
        {
            "name": "floor_user_with_mfa",
            "description": "Any User with mfaVerified MUST be permitted to callApi.",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"callApi\"",
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "floor_user_with_mfa.cedar"),
        },
        {
            "name": "floor_apikey_with_scope",
            "description": "Any ApiKey whose scopes contain 'api_call' MUST be permitted to callApi.",
            "type": "floor",
            "principal_type": "ApiKey",
            "action": "Action::\"callApi\"",
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "floor_apikey_with_scope.cedar"),
        },
        {
            "name": "floor_service_account_named",
            "description": "Any ServiceAccount with non-empty serviceName MUST be permitted to callApi.",
            "type": "floor",
            "principal_type": "ServiceAccount",
            "action": "Action::\"callApi\"",
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "floor_service_account_named.cedar"),
        },

        # ── Liveness ─────────────────────────────────────────────────────
        {
            "name": "liveness_user_call_api",
            "description": "At least one User+callApi+Resource request must be permitted.",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": "Action::\"callApi\"",
            "resource_type": "Resource",
        },
    ]
