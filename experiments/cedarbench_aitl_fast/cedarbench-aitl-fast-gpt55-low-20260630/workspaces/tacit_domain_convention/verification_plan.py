"""Hand-authored verification plan for realworld/tacit_domain_convention.

Standard RBAC for a content management system. Tests whether the planner
can unpack tacit domain shorthand:
  - "Standard RBAC" => default deny + role-keyed permits
  - "The usual hierarchy" => admin >= editor >= viewer (inheritance)
  - The per-action "minimum role" table is a FLOOR, not a tight bound

Hunts failure modes:
  - Policies that take the table literally and only permit the *exact*
    minimum role (viewer can view but editor/admin cannot, etc.)
  - Policies that grant edit/delete to too-low roles
  - Policies that omit role inheritance entirely (no admin-can-view, etc.)
  - Policies that forget default deny and permit unknown roles
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceilings ------------------------------------------------
        {
            "name": "view_safety",
            "description": (
                "view permitted only when role is viewer, editor, or admin "
                "(default deny: any other role string must not get view)"
            ),
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"view"',
            "resource_type": "Article",
            "reference_path": os.path.join(REFS, "view_safety.cedar"),
        },
        {
            "name": "edit_safety",
            "description": (
                "edit permitted only when role is editor or admin "
                "(viewer must not be permitted to edit)"
            ),
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"edit"',
            "resource_type": "Article",
            "reference_path": os.path.join(REFS, "edit_safety.cedar"),
        },
        {
            "name": "delete_safety",
            "description": (
                "delete permitted only when role is admin "
                "(viewer and editor must not be permitted to delete)"
            ),
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"delete"',
            "resource_type": "Article",
            "reference_path": os.path.join(REFS, "delete_safety.cedar"),
        },

        # -- Floors ---------------------------------------------------------
        # The "usual hierarchy" gives 6 floors (3 actions x roles >= minimum):
        #   view: viewer, editor, admin
        #   edit: editor, admin
        #   delete: admin
        {
            "name": "viewer_must_view",
            "description": "Viewer MUST be permitted to view any article",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"view"',
            "resource_type": "Article",
            "floor_path": os.path.join(REFS, "viewer_must_view.cedar"),
        },
        {
            "name": "editor_must_view",
            "description": (
                "Editor MUST be permitted to view any article "
                "(inherits viewer per the usual hierarchy)"
            ),
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"view"',
            "resource_type": "Article",
            "floor_path": os.path.join(REFS, "editor_must_view.cedar"),
        },
        {
            "name": "editor_must_edit",
            "description": "Editor MUST be permitted to edit any article",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"edit"',
            "resource_type": "Article",
            "floor_path": os.path.join(REFS, "editor_must_edit.cedar"),
        },
        {
            "name": "admin_must_view",
            "description": (
                "Admin MUST be permitted to view any article "
                "(inherits viewer per the usual hierarchy)"
            ),
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"view"',
            "resource_type": "Article",
            "floor_path": os.path.join(REFS, "admin_must_view.cedar"),
        },
        {
            "name": "admin_must_edit",
            "description": (
                "Admin MUST be permitted to edit any article "
                "(inherits editor per the usual hierarchy)"
            ),
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"edit"',
            "resource_type": "Article",
            "floor_path": os.path.join(REFS, "admin_must_edit.cedar"),
        },
        {
            "name": "admin_must_delete",
            "description": "Admin MUST be permitted to delete any article",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"delete"',
            "resource_type": "Article",
            "floor_path": os.path.join(REFS, "admin_must_delete.cedar"),
        },

        # -- Liveness -------------------------------------------------------
        {
            "name": "liveness_view",
            "description": "User+view+Article liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"view"',
            "resource_type": "Article",
        },
        {
            "name": "liveness_edit",
            "description": "User+edit+Article liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"edit"',
            "resource_type": "Article",
        },
        {
            "name": "liveness_delete",
            "description": "User+delete+Article liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"delete"',
            "resource_type": "Article",
        },
    ]
