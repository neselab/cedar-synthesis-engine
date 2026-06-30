"""Hand-authored verification plan for realworld/whitelist_and_blacklist.

Tests the conjunction of POSITIVE (whitelist) AND NEGATIVE (blacklist) set
membership on a single resource, plus a context boolean gate. Classic
allowlist-with-explicit-overrides API gateway pattern.

§8.6 note: the denylist is encoded as a per-resource attribute set, NOT
as a role-keyed forbid. There is no role intersection trap because the
negation lives on a resource attribute, not on a principal role.

Checks:
  - 1 ceiling (invoke safety: full conjunction)
  - 3 floors (positive region must be permitted, viewed from 3 angles)
  - 1 liveness
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # ── Safety ceiling ───────────────────────────────────────────────
        {
            "name": "invoke_safety",
            "description": "invoke permitted only when whitelisted AND not blacklisted AND trustedSource",
            "type": "implies",
            "principal_type": "Caller",
            "action": 'Action::"invoke"',
            "resource_type": "Endpoint",
            "reference_path": os.path.join(REFS, "invoke_safety.cedar"),
        },

        # ── Floors ───────────────────────────────────────────────────────
        {
            "name": "floor_whitelisted_invoke",
            "description": "whitelisted, non-blacklisted, trusted caller MUST be permitted",
            "type": "floor",
            "principal_type": "Caller",
            "action": 'Action::"invoke"',
            "resource_type": "Endpoint",
            "floor_path": os.path.join(REFS, "floor_whitelisted_invoke.cedar"),
        },
        {
            "name": "floor_blacklist_irrelevant_when_absent",
            "description": "blacklist must not block callers absent from it",
            "type": "floor",
            "principal_type": "Caller",
            "action": 'Action::"invoke"',
            "resource_type": "Endpoint",
            "floor_path": os.path.join(REFS, "floor_blacklist_irrelevant_when_absent.cedar"),
        },
        {
            "name": "floor_trusted_source_required",
            "description": "trusted-source caller in whitelist (not in blacklist) MUST be permitted",
            "type": "floor",
            "principal_type": "Caller",
            "action": 'Action::"invoke"',
            "resource_type": "Endpoint",
            "floor_path": os.path.join(REFS, "floor_trusted_source_required.cedar"),
        },

        # ── Liveness ─────────────────────────────────────────────────────
        {
            "name": "liveness_invoke",
            "description": "at least one invoke must be permitted",
            "type": "always-denies-liveness",
            "principal_type": "Caller",
            "action": 'Action::"invoke"',
            "resource_type": "Endpoint",
        },
    ]
