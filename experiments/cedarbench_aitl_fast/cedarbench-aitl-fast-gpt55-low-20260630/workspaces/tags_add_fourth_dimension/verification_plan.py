"""Auto-generated verification plan."""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        {
            "name": "update_workspace_safety",
            "description": "UpdateWorkspace only permitted when user is in Role-A and all four tag dimensions match",
            "type": "implies",
            "principal_type": "User",
            "action": "Action::\"UpdateWorkspace\"",
            "resource_type": "Workspace",
            "reference_path": os.path.join(REFS, "ceiling_role_a.cedar"),
        },
        {
            "name": "delete_workspace_safety",
            "description": "DeleteWorkspace only permitted when user is in Role-A and all four tag dimensions match",
            "type": "implies",
            "principal_type": "User",
            "action": "Action::\"DeleteWorkspace\"",
            "resource_type": "Workspace",
            "reference_path": os.path.join(REFS, "ceiling_role_a.cedar"),
        },
        {
            "name": "read_workspace_role_a_safety",
            "description": "ReadWorkspace only permitted when user is in Role-A with matching tags OR in Role-B with matching tags",
            "type": "implies",
            "principal_type": "User",
            "action": "Action::\"ReadWorkspace\"",
            "resource_type": "Workspace",
            "reference_path": os.path.join(REFS, "ceiling_read.cedar"),
        },
        {
            "name": "floor_role_a_update_all_wildcard",
            "description": "A user in Role-A whose Role-A tags all contain ALL must be able to UpdateWorkspace on a workspace with ALL tags",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"UpdateWorkspace\"",
            "resource_type": "Workspace",
            "floor_path": os.path.join(REFS, "floor_role_a_update.cedar"),
        },
        {
            "name": "floor_role_b_read",
            "description": "A user in Role-B whose Role-B tags all contain ALL must be able to ReadWorkspace on a workspace with ALL tags",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"ReadWorkspace\"",
            "resource_type": "Workspace",
            "floor_path": os.path.join(REFS, "floor_role_b_read.cedar"),
        },
        {
            "name": "liveness_update",
            "description": "UpdateWorkspace policy is not trivially deny-all",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": "Action::\"UpdateWorkspace\"",
            "resource_type": "Workspace",
        },
        {
            "name": "liveness_delete",
            "description": "DeleteWorkspace policy is not trivially deny-all",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": "Action::\"DeleteWorkspace\"",
            "resource_type": "Workspace",
        },
        {
            "name": "liveness_read",
            "description": "ReadWorkspace policy is not trivially deny-all",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": "Action::\"ReadWorkspace\"",
            "resource_type": "Workspace",
        },
    ]
