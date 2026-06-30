"""Auto-generated verification plan."""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        {
            "name": "update_requires_role_a",
            "description": "UpdateWorkspace is only permitted for users who are members of Role-A",
            "type": "implies",
            "principal_type": "User",
            "action": "Action::\"UpdateWorkspace\"",
            "resource_type": "Workspace",
            "reference_path": os.path.join(REFS, "ceiling_update.cedar"),
        },
        {
            "name": "delete_requires_role_a",
            "description": "DeleteWorkspace is only permitted for users who are members of Role-A",
            "type": "implies",
            "principal_type": "User",
            "action": "Action::\"DeleteWorkspace\"",
            "resource_type": "Workspace",
            "reference_path": os.path.join(REFS, "ceiling_delete.cedar"),
        },
        {
            "name": "read_requires_role_or_owner",
            "description": "ReadWorkspace is only permitted for users in Role-A, users in Role-B, or the workspace owner",
            "type": "implies",
            "principal_type": "User",
            "action": "Action::\"ReadWorkspace\"",
            "resource_type": "Workspace",
            "reference_path": os.path.join(REFS, "ceiling_read.cedar"),
        },
        {
            "name": "owner_read_floor",
            "description": "The owner of a workspace MUST always be able to ReadWorkspace on it",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"ReadWorkspace\"",
            "resource_type": "Workspace",
            "floor_path": os.path.join(REFS, "floor_owner_read.cedar"),
        },
        {
            "name": "role_a_all_tags_update_floor",
            "description": "A Role-A user whose allowedTagsForRole has Role-A with production_status containing ALL MUST be able to UpdateWorkspace on a workspace that has only production_status tags",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"UpdateWorkspace\"",
            "resource_type": "Workspace",
            "floor_path": os.path.join(REFS, "floor_role_a_update.cedar"),
        },
        {
            "name": "role_b_all_tags_read_floor",
            "description": "A Role-B user whose allowedTagsForRole has Role-B with production_status containing ALL MUST be able to ReadWorkspace on a workspace that has only production_status tags",
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
