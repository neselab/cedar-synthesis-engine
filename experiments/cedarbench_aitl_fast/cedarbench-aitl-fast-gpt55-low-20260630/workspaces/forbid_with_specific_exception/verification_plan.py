"""Hand-authored verification plan for realworld/forbid_with_specific_exception.

Tests the canonical Cedar idiom for "global forbid with a narrow exception."
A naive author writes a forbid on archived documents and tries to override
it with an owner permit, but Cedar permits cannot override forbids — the
forbid condition itself must be weakened (e.g.
`resource.archived && !(principal == resource.owner)`).

The view ceiling encodes the disjunction "(!archived) || owner-of-archived"
which forces Haiku to weaken its forbid rather than add a redundant permit.
The edit ceiling encodes "owner && !archived" — no exception at all,
so a naive `forbid when { resource.archived }` for edit is actually correct.
The contrast between the two actions is the pedagogical point.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # ── Safety ceilings ──────────────────────────────────────────────
        {
            "name": "view_safety",
            "description": "view permitted only when not archived OR owner-of-archived",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"view"',
            "resource_type": "Document",
            "reference_path": os.path.join(REFS, "view_safety.cedar"),
        },
        {
            "name": "edit_safety",
            "description": "edit permitted only when owner AND not archived",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"edit"',
            "resource_type": "Document",
            "reference_path": os.path.join(REFS, "edit_safety.cedar"),
        },

        # ── Floors ───────────────────────────────────────────────────────
        {
            "name": "floor_owner_view_unarchived",
            "description": "owner MUST view their own unarchived document",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"view"',
            "resource_type": "Document",
            "floor_path": os.path.join(REFS, "floor_owner_view_unarchived.cedar"),
        },
        {
            "name": "floor_nonowner_view_unarchived",
            "description": "any user MUST view unarchived documents (world-readable)",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"view"',
            "resource_type": "Document",
            "floor_path": os.path.join(REFS, "floor_nonowner_view_unarchived.cedar"),
        },
        {
            "name": "floor_owner_view_archived",
            "description": "owner MUST retain read-only access to archived documents",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"view"',
            "resource_type": "Document",
            "floor_path": os.path.join(REFS, "floor_owner_view_archived.cedar"),
        },
        {
            "name": "floor_owner_edit_unarchived",
            "description": "owner MUST edit their own unarchived document",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"edit"',
            "resource_type": "Document",
            "floor_path": os.path.join(REFS, "floor_owner_edit_unarchived.cedar"),
        },

        # ── Liveness ─────────────────────────────────────────────────────
        {
            "name": "liveness_view",
            "description": "at least one view permitted",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"view"',
            "resource_type": "Document",
        },
        {
            "name": "liveness_edit",
            "description": "at least one edit permitted",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"edit"',
            "resource_type": "Document",
        },
    ]
