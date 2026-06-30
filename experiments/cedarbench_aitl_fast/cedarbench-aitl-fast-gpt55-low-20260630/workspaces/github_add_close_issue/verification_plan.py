"""Auto-generated verification plan."""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # === Ceiling checks (candidate ≤ ceiling) ===
        {
            "name": "ceiling_close_issue",
            "description": "close_issue only if (reader + reporter) OR writer",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"close_issue"',
            "resource_type": "Issue",
            "reference_path": os.path.join(REFS, "ceiling_close_issue.cedar"),
        },
        {
            "name": "ceiling_push",
            "description": "Push access only for writers, blocked if repo is archived",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"push"',
            "resource_type": "Repository",
            "reference_path": os.path.join(REFS, "ceiling_push.cedar"),
        },
        {
            "name": "ceiling_edit_issue",
            "description": "Edit issue only if (reader + reporter) OR writer",
            "type": "implies",
            "principal_type": "User",
            "action": 'Action::"edit_issue"',
            "resource_type": "Issue",
            "reference_path": os.path.join(REFS, "ceiling_edit_issue.cedar"),
        },

        # === Floor checks (floor ≤ candidate) ===
        {
            "name": "floor_reporter_close",
            "description": "Readers who ARE the reporter MUST be able to close their own issue",
            "type": "floor",
            "principal_type": "User",
            "action": 'Action::"close_issue"',
            "resource_type": "Issue",
            "floor_path": os.path.join(REFS, "floor_reporter_close.cedar"),
        },

        # === Liveness checks ===
        {
            "name": "liveness_close_issue",
            "description": "close_issue is not trivially deny-all",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": 'Action::"close_issue"',
            "resource_type": "Issue",
        },
    ]
