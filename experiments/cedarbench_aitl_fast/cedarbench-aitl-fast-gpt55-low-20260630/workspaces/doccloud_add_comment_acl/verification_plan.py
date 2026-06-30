"""Auto-generated verification plan."""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # === Ceiling checks (candidate <= ceiling) ===
        {
            "name": "ceiling_comment",
            "description": "CommentOnDocument only if owner or in commentACL (authenticated)",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"CommentOnDocument"',
            "resource_type": "Document",
            "reference_path": os.path.join(REFS, "ceiling_comment.cedar"),
        },
        {
            "name": "ceiling_view",
            "description": "ViewDocument only if owner or in viewACL (authenticated User)",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"ViewDocument"',
            "resource_type": "Document",
            "reference_path": os.path.join(REFS, "ceiling_view.cedar"),
        },
        {
            "name": "ceiling_modify",
            "description": "ModifyDocument only if owner or in modifyACL (authenticated)",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"ModifyDocument"',
            "resource_type": "Document",
            "reference_path": os.path.join(REFS, "ceiling_modify.cedar"),
        },

        # === Floor checks (floor <= candidate) ===
        {
            "name": "floor_comment_acl",
            "description": "Users in commentACL MUST be able to CommentOnDocument",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"CommentOnDocument"',
            "resource_type": "Document",
            "floor_path": os.path.join(REFS, "floor_comment_acl.cedar"),
        },

        # === Liveness checks ===
        {
            "name": "liveness_comment",
            "description": "CommentOnDocument is not trivially deny-all",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"CommentOnDocument"',
            "resource_type": "Document",
        },
    ]
