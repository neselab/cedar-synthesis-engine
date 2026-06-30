"""Auto-generated verification plan."""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        {
            "name": "update_workspace_safety",
            "description": "UpdateWorkspace is only permitted for Role-A members whose Role-A tags match the workspace tags",
            "type": "implies",
            "principal_type": "User",
            "action": "Action::\"UpdateWorkspace\"",
            "resource_type": "Workspace",
            "reference_path": os.path.join(REFS, "ceiling_update_workspace.cedar"),
        },
        {
            "name": "delete_workspace_safety",
            "description": "DeleteWorkspace is only permitted for Role-A members whose Role-A tags match the workspace tags",
            "type": "implies",
            "principal_type": "User",
            "action": "Action::\"DeleteWorkspace\"",
            "resource_type": "Workspace",
            "reference_path": os.path.join(REFS, "ceiling_delete_workspace.cedar"),
        },
        {
            "name": "read_workspace_safety",
            "description": "ReadWorkspace is only permitted for Role-A members with matching Role-A tags OR Role-B members with matching Role-B tags",
            "type": "implies",
            "principal_type": "User",
            "action": "Action::\"ReadWorkspace\"",
            "resource_type": "Workspace",
            "reference_path": os.path.join(REFS, "ceiling_read_workspace.cedar"),
        },
        {
            "name": "role_a_update_floor",
            "description": "A Role-A member with the allowedTagsForRole Role-A record present but no sub-tags defined MUST be permitted to UpdateWorkspace on a workspace with no tags",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"UpdateWorkspace\"",
            "resource_type": "Workspace",
            "floor_path": os.path.join(REFS, "floor_role_a_update.cedar"),
        },
        {
            "name": "role_a_delete_floor",
            "description": "A Role-A member with the allowedTagsForRole Role-A record present but no sub-tags defined MUST be permitted to DeleteWorkspace on a workspace with no tags",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"DeleteWorkspace\"",
            "resource_type": "Workspace",
            "floor_path": os.path.join(REFS, "floor_role_a_delete.cedar"),
        },
        {
            "name": "role_b_read_floor",
            "description": "A Role-B member with the allowedTagsForRole Role-B record present but no sub-tags MUST be permitted to ReadWorkspace on a workspace with no tags",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"ReadWorkspace\"",
            "resource_type": "Workspace",
            "floor_path": os.path.join(REFS, "floor_role_b_read.cedar"),
        },
        {
            "name": "role_a_read_floor_with_all_wildcard",
            "description": "A Role-A member whose Role-A production_status contains ALL MUST be permitted to ReadWorkspace on a workspace whose production_status is any set, when other tag groups are absent on both sides",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"ReadWorkspace\"",
            "resource_type": "Workspace",
            "floor_path": os.path.join(REFS, "floor_role_a_read_all_wildcard.cedar"),
        },
        {
            "name": "liveness_update_workspace",
            "description": "UpdateWorkspace policy is not trivially deny-all",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": "Action::\"UpdateWorkspace\"",
            "resource_type": "Workspace",
        },
        {
            "name": "liveness_delete_workspace",
            "description": "DeleteWorkspace policy is not trivially deny-all",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": "Action::\"DeleteWorkspace\"",
            "resource_type": "Workspace",
        },
        {
            "name": "liveness_read_workspace",
            "description": "ReadWorkspace policy is not trivially deny-all",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": "Action::\"ReadWorkspace\"",
            "resource_type": "Workspace",
        },
    ]
