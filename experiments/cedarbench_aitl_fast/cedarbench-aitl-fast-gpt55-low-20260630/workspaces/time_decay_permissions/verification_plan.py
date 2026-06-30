"""Hand-authored verification plan for realworld/time_decay_permissions.

Time-decaying permissions: an Operator's set of permitted actions on a
Resource degrades as their authentication credential ages. Three tiers,
keyed off `context.now.durationSince(principal.lastAuthAt)`:

  * Fresh   (age < 1h):       all actions for any sensitivity
  * Stale   (1h <= age < 4h): read for any sensitivity; write/delete
                              ONLY for sensitivity == 1
  * Expired (age >= 4h):      no actions

Failure modes hunted:
  * Candidate omits the sign guard (context.now >= principal.lastAuthAt)
    and the negative-duration < positive-duration comparison silently
    permits pre-auth requests.
  * Candidate uses ISO 8601 duration syntax (duration("PT1H") / "PT4H"),
    which Cedar rejects in favor of Go-style ("1h" / "4h").
  * Candidate collapses fresh+stale into a single 4h tier and forgets
    that stale write/delete is gated on sensitivity == 1.
  * Candidate gates read on sensitivity (over-restriction) when read
    is sensitivity-agnostic in both fresh and stale windows.
  * Candidate uses <= instead of < at the boundaries (the spec adopts
    the strict-less-than convention).

11 checks total (3 ceilings + 5 floors + 3 liveness).
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceilings (one per action) --------------------------------
        {
            "name": "read_safety",
            "description": (
                "read permitted only when context.now >= principal.lastAuthAt "
                "AND context.now.durationSince(principal.lastAuthAt) "
                "< duration('4h'); sensitivity is irrelevant for read"
            ),
            "type": "implies",
            "principal_type": "Operator",
            "action": 'Action::"read"',
            "resource_type": "Resource",
            "reference_path": os.path.join(REFS, "read_safety.cedar"),
        },
        {
            "name": "write_safety",
            "description": (
                "write permitted only when context.now >= principal.lastAuthAt "
                "AND (age < 1h OR (age < 4h AND resource.sensitivity == 1))"
            ),
            "type": "implies",
            "principal_type": "Operator",
            "action": 'Action::"write"',
            "resource_type": "Resource",
            "reference_path": os.path.join(REFS, "write_safety.cedar"),
        },
        {
            "name": "delete_safety",
            "description": (
                "delete permitted only when context.now >= principal.lastAuthAt "
                "AND (age < 1h OR (age < 4h AND resource.sensitivity == 1))"
            ),
            "type": "implies",
            "principal_type": "Operator",
            "action": 'Action::"delete"',
            "resource_type": "Resource",
            "reference_path": os.path.join(REFS, "delete_safety.cedar"),
        },

        # -- Floors (positive assertions) -----------------------------------
        {
            "name": "floor_fresh_read_high_sensitivity",
            "description": (
                "Concrete probe: fresh window (30 min since lastAuthAt) + "
                "read on sensitivity-3 resource MUST be permitted"
            ),
            "type": "floor",
            "principal_type": "Operator",
            "action": 'Action::"read"',
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "floor_fresh_read_high_sensitivity.cedar"),
        },
        {
            "name": "floor_fresh_write_high_sensitivity",
            "description": (
                "Concrete probe: fresh window (30 min since lastAuthAt) + "
                "write on sensitivity-3 resource MUST be permitted"
            ),
            "type": "floor",
            "principal_type": "Operator",
            "action": 'Action::"write"',
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "floor_fresh_write_high_sensitivity.cedar"),
        },
        {
            "name": "floor_fresh_delete_high_sensitivity",
            "description": (
                "Concrete probe: fresh window (30 min since lastAuthAt) + "
                "delete on sensitivity-3 resource MUST be permitted"
            ),
            "type": "floor",
            "principal_type": "Operator",
            "action": 'Action::"delete"',
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "floor_fresh_delete_high_sensitivity.cedar"),
        },
        {
            "name": "floor_stale_read_high_sensitivity",
            "description": (
                "Concrete probe: stale window (2h since lastAuthAt) + read "
                "on sensitivity-3 resource MUST be permitted (read is "
                "sensitivity-agnostic in the stale window)"
            ),
            "type": "floor",
            "principal_type": "Operator",
            "action": 'Action::"read"',
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "floor_stale_read_high_sensitivity.cedar"),
        },
        {
            "name": "floor_stale_write_low_sensitivity",
            "description": (
                "Concrete probe: stale window (2h since lastAuthAt) + write "
                "on sensitivity-1 resource MUST be permitted (stale write "
                "is gated on sensitivity == 1)"
            ),
            "type": "floor",
            "principal_type": "Operator",
            "action": 'Action::"write"',
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "floor_stale_write_low_sensitivity.cedar"),
        },

        # -- Liveness -------------------------------------------------------
        {
            "name": "liveness_read",
            "description": "Operator+read+Resource liveness",
            "type": "always-denies-liveness",
            "principal_type": "Operator",
            "action": 'Action::"read"',
            "resource_type": "Resource",
        },
        {
            "name": "liveness_write",
            "description": "Operator+write+Resource liveness",
            "type": "always-denies-liveness",
            "principal_type": "Operator",
            "action": 'Action::"write"',
            "resource_type": "Resource",
        },
        {
            "name": "liveness_delete",
            "description": "Operator+delete+Resource liveness",
            "type": "always-denies-liveness",
            "principal_type": "Operator",
            "action": 'Action::"delete"',
            "resource_type": "Resource",
        },
    ]
