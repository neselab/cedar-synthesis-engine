"""Hand-authored verification plan for realworld/stale_cache_invalidation.

Cached-authorization staleness pattern. Authorization decisions are
cached for performance, but the freshness window varies sharply by
action sensitivity:
  - read tolerates a 5-minute cache window.
  - writeCritical demands a 60-second cache window.
  - delete bypasses the cache entirely and instead demands a fresh
    (< 30s) MFA attestation plus admin role.

Both authCacheTimestamp and mfaTimestamp are OPTIONAL context
attributes per §8.3 — every read must be has-guarded.

The common failure modes this scenario hunts:
  - Candidate forgets has-guard on optional timestamp (rejected by
    the type-checker, surfaces as a Cedar validation error).
  - Candidate uses ISO 8601 ("PT5M") instead of Go-style ("5m") for
    duration() literals (§8.9).
  - Candidate conflates the three time windows or shares a single
    cache window across actions.
  - Candidate permits delete without MFA, or without role check, or
    without freshness check.
  - Candidate uses authCacheTimestamp for delete (the spec forbids it
    — delete must consult mfaTimestamp only).

10 checks total (3 ceilings + 4 floors + 3 liveness).
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceilings ------------------------------------------------
        {
            "name": "read_safety",
            "description": "read permitted only when authCacheTimestamp present AND now.durationSince(authCacheTimestamp) < 5m",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"read"',
            "resource_type": "Resource",
            "reference_path": os.path.join(REFS, "read_safety.cedar"),
        },
        {
            "name": "writecritical_safety",
            "description": "writeCritical permitted only when authCacheTimestamp present AND now.durationSince(authCacheTimestamp) < 60s",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"writeCritical"',
            "resource_type": "Resource",
            "reference_path": os.path.join(REFS, "writecritical_safety.cedar"),
        },
        {
            "name": "delete_safety",
            "description": "delete permitted only when role == admin AND mfaTimestamp present AND now.durationSince(mfaTimestamp) < 30s",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"delete"',
            "resource_type": "Resource",
            "reference_path": os.path.join(REFS, "delete_safety.cedar"),
        },

        # -- Floors (positive assertions) -----------------------------------
        {
            "name": "fresh_cache_must_read",
            "description": "Any User with a < 5m fresh authCacheTimestamp MUST be permitted to read",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"read"',
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "fresh_cache_must_read.cedar"),
        },
        {
            "name": "very_fresh_cache_must_read",
            "description": "Any User with a < 60s fresh authCacheTimestamp MUST be permitted to read (subset anchor)",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"read"',
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "very_fresh_cache_must_read.cedar"),
        },
        {
            "name": "fresh_cache_must_writecritical",
            "description": "Any User with a < 60s fresh authCacheTimestamp MUST be permitted to writeCritical",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"writeCritical"',
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "fresh_cache_must_writecritical.cedar"),
        },
        {
            "name": "admin_fresh_mfa_must_delete",
            "description": "An admin User with a < 30s fresh mfaTimestamp MUST be permitted to delete",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"delete"',
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "admin_fresh_mfa_must_delete.cedar"),
        },

        # -- Liveness -------------------------------------------------------
        {
            "name": "liveness_read",
            "description": "User+read+Resource liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"read"',
            "resource_type": "Resource",
        },
        {
            "name": "liveness_writecritical",
            "description": "User+writeCritical+Resource liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"writeCritical"',
            "resource_type": "Resource",
        },
        {
            "name": "liveness_delete",
            "description": "User+delete+Resource liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"delete"',
            "resource_type": "Resource",
        },
    ]
