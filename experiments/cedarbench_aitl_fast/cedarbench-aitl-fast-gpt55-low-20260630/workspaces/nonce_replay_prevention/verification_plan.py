"""Hand-authored verification plan for realworld/nonce_replay_prevention.

Nonce-based replay prevention with three distinct authorization states:
  1. context lacks `nonce`                          -> deny (no recency proof)
  2. context.nonce NOT in resource.validNonces      -> deny (replay/forged)
  3. context.nonce IN resource.validNonces          -> permit

Cedar idiom: optional context attribute requires has-guard before read
(§8.3 in docs/harness_fix_log.md).

4 checks: 1 ceiling + 2 floors + 1 liveness.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceiling ---------------------------------------------------
        {
            "name": "invoke_safety",
            "description": (
                "invoke permitted only when context has nonce AND "
                "resource.validNonces.contains(context.nonce). Rules out "
                "the missing-nonce and unknown-nonce deny states."
            ),
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"invoke"',
            "resource_type": "CriticalEndpoint",
            "reference_path": os.path.join(REFS, "invoke_safety.cedar"),
        },

        # -- Floors ------------------------------------------------------------
        {
            "name": "valid_nonce_must_invoke",
            "description": (
                "A request whose context.nonce is in the endpoint's "
                "validNonces MUST be permitted to invoke."
            ),
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"invoke"',
            "resource_type": "CriticalEndpoint",
            "floor_path": os.path.join(REFS, "valid_nonce_must_invoke.cedar"),
        },
        {
            "name": "any_user_with_valid_nonce_must_invoke",
            "description": (
                "ANY User (no per-principal gating) with a valid nonce MUST "
                "be permitted to invoke -- nonce possession alone authorizes."
            ),
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"invoke"',
            "resource_type": "CriticalEndpoint",
            "floor_path": os.path.join(REFS, "any_user_with_valid_nonce_must_invoke.cedar"),
        },

        # -- Liveness ----------------------------------------------------------
        {
            "name": "liveness_invoke",
            "description": "User+invoke+CriticalEndpoint liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"invoke"',
            "resource_type": "CriticalEndpoint",
        },
    ]
