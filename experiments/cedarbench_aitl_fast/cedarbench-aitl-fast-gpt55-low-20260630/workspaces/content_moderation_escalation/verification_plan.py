"""Hand-authored verification plan for realworld/content_moderation_escalation.

Tiered content moderation: trust level vs severity threshold, with
unconditional escalation and lead-only override.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # ── Safety ceilings ──────────────────────────────────────────────
        {"name": "review_safety", "description": "review only when trust level meets severity threshold", "type": "implies", "principal_type": "Moderator", "action": 'Action::"review"', "resource_type": "ContentReport", "reference_path": os.path.join(REFS, "review_safety.cedar")},
        {"name": "resolve_safety", "description": "resolve under same threshold as review", "type": "implies", "principal_type": "Moderator", "action": 'Action::"resolve"', "resource_type": "ContentReport", "reference_path": os.path.join(REFS, "resolve_safety.cedar")},
        {"name": "escalate_safety", "description": "any moderator can escalate", "type": "implies", "principal_type": "Moderator", "action": 'Action::"escalate"', "resource_type": "ContentReport", "reference_path": os.path.join(REFS, "escalate_safety.cedar")},
        {"name": "override_safety", "description": "override only when lead (trustLevel >= 3)", "type": "implies", "principal_type": "Moderator", "action": 'Action::"override"', "resource_type": "ContentReport", "reference_path": os.path.join(REFS, "override_safety.cedar")},

        # ── Floors ───────────────────────────────────────────────────────
        {"name": "floor_junior_review_low", "description": "junior mod MUST review severity <= 2", "type": "floor", "principal_type": "Moderator", "action": 'Action::"review"', "resource_type": "ContentReport", "floor_path": os.path.join(REFS, "floor_junior_review_low.cedar")},
        {"name": "floor_senior_review_medium", "description": "senior mod MUST review severity <= 4", "type": "floor", "principal_type": "Moderator", "action": 'Action::"review"', "resource_type": "ContentReport", "floor_path": os.path.join(REFS, "floor_senior_review_medium.cedar")},
        {"name": "floor_any_escalate", "description": "any mod MUST escalate", "type": "floor", "principal_type": "Moderator", "action": 'Action::"escalate"', "resource_type": "ContentReport", "floor_path": os.path.join(REFS, "floor_any_escalate.cedar")},
        {"name": "floor_lead_override", "description": "lead mod MUST override", "type": "floor", "principal_type": "Moderator", "action": 'Action::"override"', "resource_type": "ContentReport", "floor_path": os.path.join(REFS, "floor_lead_override.cedar")},

        # ── Liveness ─────────────────────────────────────────────────────
        {"name": "liveness_review", "description": "at least one review permitted", "type": "always-denies-liveness", "principal_type": "Moderator", "action": 'Action::"review"', "resource_type": "ContentReport"},
        {"name": "liveness_resolve", "description": "at least one resolve permitted", "type": "always-denies-liveness", "principal_type": "Moderator", "action": 'Action::"resolve"', "resource_type": "ContentReport"},
        {"name": "liveness_escalate", "description": "at least one escalate permitted", "type": "always-denies-liveness", "principal_type": "Moderator", "action": 'Action::"escalate"', "resource_type": "ContentReport"},
        {"name": "liveness_override", "description": "at least one override permitted", "type": "always-denies-liveness", "principal_type": "Moderator", "action": 'Action::"override"', "resource_type": "ContentReport"},
    ]
