"""Hand-authored verification plan for realworld/enumerated_status_entity.

Document lifecycle gated by an enumerated entity status. Tests:
  - Cedar enumerated entity types (Status enum ["active","pending","archived"])
  - Equality on enum entity literals (resource.currentStatus == Status::"active")
  - Lifecycle/state-machine constraints (archive only on active, reactivate only on archived)
  - Role-based unlock (admin sees pending/archived)

Hunts failure modes:
  - Policies that try to access attributes on enum entities (Status::"active".name)
  - Policies that use string equality (resource.currentStatus == "active") instead of entity equality
  - Policies that allow archive on already-archived or pending docs
  - Policies that allow reactivate on active or pending docs
  - Policies that let non-admins view pending/archived docs
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceilings ------------------------------------------------
        {
            "name": "view_safety",
            "description": (
                "view permitted only when status==active OR "
                "(role==admin AND status in {pending, archived})"
            ),
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"view"',
            "resource_type": "Document",
            "reference_path": os.path.join(REFS, "ceiling_view.cedar"),
        },
        {
            "name": "archive_safety",
            "description": "archive permitted only when role==admin AND status==active",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"archive"',
            "resource_type": "Document",
            "reference_path": os.path.join(REFS, "ceiling_archive.cedar"),
        },
        {
            "name": "reactivate_safety",
            "description": "reactivate permitted only when role==admin AND status==archived",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"reactivate"',
            "resource_type": "Document",
            "reference_path": os.path.join(REFS, "ceiling_reactivate.cedar"),
        },

        # -- Floors ---------------------------------------------------------
        {
            "name": "any_user_views_active",
            "description": "Any user MUST be permitted to view an active document",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"view"',
            "resource_type": "Document",
            "floor_path": os.path.join(REFS, "floor_view_active.cedar"),
        },
        {
            "name": "admin_views_pending_or_archived",
            "description": "Admin MUST be permitted to view pending and archived documents",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"view"',
            "resource_type": "Document",
            "floor_path": os.path.join(REFS, "floor_admin_view_pending.cedar"),
        },
        {
            "name": "admin_archives_active",
            "description": "Admin MUST be permitted to archive an active document",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"archive"',
            "resource_type": "Document",
            "floor_path": os.path.join(REFS, "floor_admin_archive.cedar"),
        },
        {
            "name": "admin_reactivates_archived",
            "description": "Admin MUST be permitted to reactivate an archived document",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"reactivate"',
            "resource_type": "Document",
            "floor_path": os.path.join(REFS, "floor_admin_reactivate.cedar"),
        },

        # -- Liveness -------------------------------------------------------
        {
            "name": "liveness_view",
            "description": "User+view+Document liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"view"',
            "resource_type": "Document",
        },
        {
            "name": "liveness_archive",
            "description": "User+archive+Document liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"archive"',
            "resource_type": "Document",
        },
        {
            "name": "liveness_reactivate",
            "description": "User+reactivate+Document liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"reactivate"',
            "resource_type": "Document",
        },
    ]
