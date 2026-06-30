"""Auto-generated verification plan."""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # === Ceiling checks (candidate <= ceiling) ===
        {
            "name": "ceiling_edit_presentation",
            "description": "editPresentation only if owner or editor AND not archived",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"editPresentation"',
            "resource_type": "Presentation",
            "reference_path": os.path.join(REFS, "ceiling_edit_presentation.cedar"),
        },
        {
            "name": "ceiling_grant_view",
            "description": "grantViewAccessToPresentation only if owner or editor AND not archived",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"grantViewAccessToPresentation"',
            "resource_type": "Presentation",
            "reference_path": os.path.join(REFS, "ceiling_grant_view.cedar"),
        },

        # === Floor checks (floor <= candidate) ===
        {
            "name": "floor_view_archived",
            "description": "Viewers MUST still be able to view archived presentations",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"viewPresentation"',
            "resource_type": "Presentation",
            "floor_path": os.path.join(REFS, "floor_view_archived.cedar"),
        },

        # === Liveness checks ===
        {
            "name": "liveness_edit",
            "description": "editPresentation is not trivially deny-all",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"editPresentation"',
            "resource_type": "Presentation",
        },
        {
            "name": "liveness_view",
            "description": "viewPresentation is not trivially deny-all",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"viewPresentation"',
            "resource_type": "Presentation",
        },
    ]
