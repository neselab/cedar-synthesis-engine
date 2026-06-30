"""Auto-generated verification plan."""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        {
            "name": "update_workspace_safety",
            "description": "UpdateWorkspace only allowed for Role-A members with tag match, sensitivity <= 3, and workspace approved",
            "type": "implies",
            "principal_type": "User",
            "action": "Action::\"UpdateWorkspace\"",
            "resource_type": "Workspace",
            "reference_path": os.path.join(REFS, "ceiling_update.cedar"),
        },
        {
            "name": "delete_workspace_safety",
            "description": "DeleteWorkspace only allowed for Role-A members with tag match, sensitivity <= 3, and workspace approved",
            "type": "implies",
            "principal_type": "User",
            "action": "Action::\"DeleteWorkspace\"",
            "resource_type": "Workspace",
            "reference_path": os.path.join(REFS, "ceiling_delete.cedar"),
        },
        {
            "name": "read_workspace_safety",
            "description": "ReadWorkspace only allowed if owner OR (Role-A member with tag match and sensitivity <= 3) OR (Role-B member with tag match and sensitivity <= 1)",
            "type": "implies",
            "principal_type": "User",
            "action": "Action::\"ReadWorkspace\"",
            "resource_type": "Workspace",
            "reference_path": os.path.join(REFS, "ceiling_read.cedar"),
        },
        {
            "name": "approval_gate_update",
            "description": "UpdateWorkspace is never allowed on unapproved workspaces",
            "type": "implies",
            "principal_type": "User",
            "action": "Action::\"UpdateWorkspace\"",
            "resource_type": "Workspace",
            "reference_path": os.path.join(REFS, "ceiling_update_approved.cedar"),
        },
        {
            "name": "approval_gate_delete",
            "description": "DeleteWorkspace is never allowed on unapproved workspaces",
            "type": "implies",
            "principal_type": "User",
            "action": "Action::\"DeleteWorkspace\"",
            "resource_type": "Workspace",
            "reference_path": os.path.join(REFS, "ceiling_delete_approved.cedar"),
        },
        {
            "name": "owner_read_floor",
            "description": "Owner MUST be able to ReadWorkspace on their own workspace regardless of tags, sensitivity, or roles (but approval gate does not block reads)",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"ReadWorkspace\"",
            "resource_type": "Workspace",
            "floor_path": os.path.join(REFS, "floor_owner_read.cedar"),
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
