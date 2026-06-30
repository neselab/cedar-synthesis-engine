"""Hand-authored verification plan for realworld/specification_ambiguity_needs_counterexample.

Tests a scenario where the natural-language specification admits two
readings -- a logical OR (intended) and a logical AND (over-restrictive)
-- and only a specific counterexample (an editor who does NOT own the
document) discriminates between them.

5 checks: 1 ceiling + 3 floors + 1 liveness.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceiling ----------------------------------------------------
        {
            "name": "edit_ceiling",
            "description": "edit permitted only when (principal.role == \"editor\") OR (principal == resource.owner)",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"edit"',
            "resource_type": "Document",
            "reference_path": os.path.join(REFS, "edit_ceiling.cedar"),
        },

        # -- Floors ------------------------------------------------------------
        {
            "name": "floor_editor_non_owner",
            "description": "Editor who is NOT the owner MUST be permitted to edit (the discriminating counterexample)",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"edit"',
            "resource_type": "Document",
            "floor_path": os.path.join(REFS, "floor_editor_non_owner.cedar"),
        },
        {
            "name": "floor_owner_non_editor",
            "description": "Owner who is NOT an editor MUST be permitted to edit",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"edit"',
            "resource_type": "Document",
            "floor_path": os.path.join(REFS, "floor_owner_non_editor.cedar"),
        },
        {
            "name": "floor_editor_owner",
            "description": "Editor who is also the owner MUST be permitted to edit (trivial overlap)",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"edit"',
            "resource_type": "Document",
            "floor_path": os.path.join(REFS, "floor_editor_owner.cedar"),
        },

        # -- Liveness ----------------------------------------------------------
        {
            "name": "liveness_edit",
            "description": "User+edit+Document liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"edit"',
            "resource_type": "Document",
        },
    ]
