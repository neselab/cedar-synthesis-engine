"""Auto-generated verification plan."""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        {
            "name": "update_workspace_safety",
            "description": "UpdateWorkspace only permitted for Role-A members with matching tags across all dimensions",
            "type": "implies",
            "principal_type": "User",
            "action": "Action::\"UpdateWorkspace\"",
            "resource_type": "Workspace",
            "reference_path": os.path.join(REFS, "ceiling_role_a_actions.cedar"),
        },
        {
            "name": "delete_workspace_safety",
            "description": "DeleteWorkspace only permitted for Role-A members with matching tags across all dimensions",
            "type": "implies",
            "principal_type": "User",
            "action": "Action::\"DeleteWorkspace\"",
            "resource_type": "Workspace",
            "reference_path": os.path.join(REFS, "ceiling_role_a_actions.cedar"),
        },
        {
            "name": "read_workspace_safety",
            "description": "ReadWorkspace only permitted for Role-A members with Role-A tag match OR Role-B members with Role-B tag match",
            "type": "implies",
            "principal_type": "User",
            "action": "Action::\"ReadWorkspace\"",
            "resource_type": "Workspace",
            "reference_path": os.path.join(REFS, "ceiling_read_workspace.cedar"),
        },
        {
            "name": "floor_role_a_update",
            "description": "A Role-A user whose tags fully match the workspace MUST be allowed to UpdateWorkspace",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"UpdateWorkspace\"",
            "resource_type": "Workspace",
            "floor_path": os.path.join(REFS, "floor_role_a_actions.cedar"),
        },
        {
            "name": "floor_role_a_delete",
            "description": "A Role-A user whose tags fully match the workspace MUST be allowed to DeleteWorkspace",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"DeleteWorkspace\"",
            "resource_type": "Workspace",
            "floor_path": os.path.join(REFS, "floor_role_a_actions.cedar"),
        },
        {
            "name": "floor_role_b_read",
            "description": "A Role-B user whose Role-B tags fully match the workspace MUST be allowed to ReadWorkspace",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"ReadWorkspace\"",
            "resource_type": "Workspace",
            "floor_path": os.path.join(REFS, "floor_role_b_read.cedar"),
        },
        {
            "name": "liveness_update_workspace",
            "description": "UpdateWorkspace is not trivially denied for all requests",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": "Action::\"UpdateWorkspace\"",
            "resource_type": "Workspace",
        },
        {
            "name": "liveness_delete_workspace",
            "description": "DeleteWorkspace is not trivially denied for all requests",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": "Action::\"DeleteWorkspace\"",
            "resource_type": "Workspace",
        },
        {
            "name": "liveness_read_workspace",
            "description": "ReadWorkspace is not trivially denied for all requests",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": "Action::\"ReadWorkspace\"",
            "resource_type": "Workspace",
        },
    ]
