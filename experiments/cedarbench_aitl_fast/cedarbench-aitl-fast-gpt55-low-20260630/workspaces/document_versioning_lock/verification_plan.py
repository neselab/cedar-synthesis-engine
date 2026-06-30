"""Hand-authored verification plan for realworld/document_versioning_lock.

Content management system with exclusive edit locks and draft-state gating.
Tests:
  - Role-gated actions (viewer vs editor vs admin)
  - Boolean lock flag with owner-based bypass
  - Draft-state precondition on publish
  - Admin override on unlock

The central safety property: edit is permitted only when the document is
unlocked OR locked by the requesting user. A candidate that ignores the
lock flag or allows any editor/admin to edit regardless of lock holder is
incorrect.

11 checks: 5 ceilings + 3 floors + 3 liveness.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # ── Safety ceilings (one per action) ────────────────────────────
        {
            "name": "read_safety",
            "description": "read permitted for any User on any Document (no restrictions)",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"read"',
            "resource_type": "Document",
            "reference_path": os.path.join(REFS, "read_safety.cedar"),
        },
        {
            "name": "edit_safety",
            "description": "edit permitted only for editor/admin AND document is unlocked or locked by this user",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"edit"',
            "resource_type": "Document",
            "reference_path": os.path.join(REFS, "edit_safety.cedar"),
        },
        {
            "name": "lock_safety",
            "description": "lock permitted only for editor/admin",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"lock"',
            "resource_type": "Document",
            "reference_path": os.path.join(REFS, "lock_safety.cedar"),
        },
        {
            "name": "unlock_safety",
            "description": "unlock permitted only when principal is lock holder or admin",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"unlock"',
            "resource_type": "Document",
            "reference_path": os.path.join(REFS, "unlock_safety.cedar"),
        },
        {
            "name": "publish_safety",
            "description": "publish permitted only for admin AND document is draft",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"publish"',
            "resource_type": "Document",
            "reference_path": os.path.join(REFS, "publish_safety.cedar"),
        },

        # ── Floors (positive assertions about what must be permitted) ───
        {
            "name": "floor_editor_edit",
            "description": "Editor MUST be permitted to edit an unlocked document",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"edit"',
            "resource_type": "Document",
            "floor_path": os.path.join(REFS, "floor_editor_edit.cedar"),
        },
        {
            "name": "floor_admin_unlock",
            "description": "Admin MUST be permitted to unlock any document",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"unlock"',
            "resource_type": "Document",
            "floor_path": os.path.join(REFS, "floor_admin_unlock.cedar"),
        },
        {
            "name": "floor_admin_publish_draft",
            "description": "Admin MUST be permitted to publish a draft document",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"publish"',
            "resource_type": "Document",
            "floor_path": os.path.join(REFS, "floor_admin_publish_draft.cedar"),
        },

        # ── Liveness ────────────────────────────────────────────────────
        {
            "name": "liveness_edit",
            "description": "User+edit+Document has at least one permitted request",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"edit"',
            "resource_type": "Document",
        },
        {
            "name": "liveness_unlock",
            "description": "User+unlock+Document has at least one permitted request",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"unlock"',
            "resource_type": "Document",
        },
        {
            "name": "liveness_publish",
            "description": "User+publish+Document has at least one permitted request",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"publish"',
            "resource_type": "Document",
        },
    ]
