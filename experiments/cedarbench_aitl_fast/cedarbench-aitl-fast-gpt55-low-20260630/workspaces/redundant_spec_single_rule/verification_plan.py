"""Hand-authored verification plan for realworld/redundant_spec_single_rule.

The spec restates the SAME owner-only read rule three different ways.
The planner is being tested on its ability to recognize the redundancy
and encode the rule ONCE rather than three times.

The verification plan therefore has exactly:
  - 1 ceiling encoding the single rule (principal == resource.owner)
  - 1 floor for the owner liveness (same rule)
  - 1 liveness check for read

Three checks total. If a future planner tried to enforce three separate
ceilings (one per restatement), the redundancy would be visible here as
duplication — that is the anti-pattern this scenario guards against.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # ── Safety ceiling (single rule, encoded ONCE) ────────────────────
        {
            "name": "read_safety",
            "description": "read permitted only when principal == resource.owner",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"read"',
            "resource_type": "Document",
            "reference_path": os.path.join(REFS, "read_safety.cedar"),
        },

        # ── Floor (same single rule) ──────────────────────────────────────
        {
            "name": "floor_owner_read",
            "description": "owner MUST be able to read their document",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"read"',
            "resource_type": "Document",
            "floor_path": os.path.join(REFS, "floor_owner_read.cedar"),
        },

        # ── Liveness ──────────────────────────────────────────────────────
        {
            "name": "liveness_read",
            "description": "at least one read permitted",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"read"',
            "resource_type": "Document",
        },
    ]
