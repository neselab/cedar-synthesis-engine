"""Hand-authored verification plan for realworld/set_contains_any.

Tests Cedar's .containsAny() set operation (first use in benchmark),
alongside .containsAll() for elevated access. Tag-based access with
set-intersection semantics.

Checks:
  - 3 ceilings (read/write/manageTags safety)
  - 3 floors (read overlap, write expert, owner manage)
  - 3 liveness
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # ── Safety ceilings ──────────────────────────────────────────────
        {
            "name": "read_safety",
            "description": "read permitted only when interest tags overlap AND clearance sufficient",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"read"',
            "resource_type": "Document",
            "reference_path": os.path.join(REFS, "read_safety.cedar"),
        },
        {
            "name": "write_safety",
            "description": "write permitted only when interest tags contain ALL topic tags AND clearance sufficient",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"write"',
            "resource_type": "Document",
            "reference_path": os.path.join(REFS, "write_safety.cedar"),
        },
        {
            "name": "manage_tags_safety",
            "description": "manageTags permitted only when owner",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"manageTags"',
            "resource_type": "Document",
            "reference_path": os.path.join(REFS, "manage_tags_safety.cedar"),
        },

        # ── Floors ───────────────────────────────────────────────────────
        {
            "name": "floor_read_overlap",
            "description": "user with overlapping interests AND clearance MUST read",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"read"',
            "resource_type": "Document",
            "floor_path": os.path.join(REFS, "floor_read_overlap.cedar"),
        },
        {
            "name": "floor_write_expert",
            "description": "user with all topic tags AND clearance MUST write",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"write"',
            "resource_type": "Document",
            "floor_path": os.path.join(REFS, "floor_write_expert.cedar"),
        },
        {
            "name": "floor_owner_manage",
            "description": "owner MUST manage tags",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"manageTags"',
            "resource_type": "Document",
            "floor_path": os.path.join(REFS, "floor_owner_manage.cedar"),
        },

        # ── Liveness ─────────────────────────────────────────────────────
        {
            "name": "liveness_read",
            "description": "at least one read must be permitted",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"read"',
            "resource_type": "Document",
        },
        {
            "name": "liveness_write",
            "description": "at least one write must be permitted",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"write"',
            "resource_type": "Document",
        },
        {
            "name": "liveness_manage",
            "description": "at least one manageTags must be permitted",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"manageTags"',
            "resource_type": "Document",
        },
    ]
