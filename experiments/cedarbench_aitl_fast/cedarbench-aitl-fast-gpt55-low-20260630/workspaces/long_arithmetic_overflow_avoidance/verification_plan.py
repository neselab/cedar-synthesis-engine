"""Hand-authored verification plan for realworld/long_arithmetic_overflow_avoidance.

Project budget tracking that stresses overflow-safe Cedar Long arithmetic.
The naive form `spentSoFar + requestedAmount <= monthlyBudget` can overflow
at runtime (Cedar Long is signed 64-bit, no overflow detection at validation,
runtime overflow errors out the policy and silently denies). The safe form
rewrites as `requestedAmount <= monthlyBudget - spentSoFar` guarded by
`spentSoFar < monthlyBudget`.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # ── Safety ceilings ──────────────────────────────────────────────
        {"name": "request_spend_safety", "description": "requestSpend permitted only with safe in-budget arithmetic", "type": "implies", "principal_type": "Approver", "action": 'Action::"requestSpend"', "resource_type": "Project", "reference_path": os.path.join(REFS, "request_spend_safety.cedar")},
        {"name": "approve_spend_safety", "description": "approveSpend requires admin AND safe in-budget arithmetic", "type": "implies", "principal_type": "Approver", "action": 'Action::"approveSpend"', "resource_type": "Project", "reference_path": os.path.join(REFS, "approve_spend_safety.cedar")},

        # ── Floors ───────────────────────────────────────────────────────
        {"name": "floor_member_request_in_budget", "description": "member with positive in-budget request MUST requestSpend", "type": "floor", "principal_type": "Approver", "action": 'Action::"requestSpend"', "resource_type": "Project", "floor_path": os.path.join(REFS, "floor_member_request_in_budget.cedar")},
        {"name": "floor_admin_request_in_budget", "description": "admin with positive in-budget request MUST requestSpend", "type": "floor", "principal_type": "Approver", "action": 'Action::"requestSpend"', "resource_type": "Project", "floor_path": os.path.join(REFS, "floor_admin_request_in_budget.cedar")},
        {"name": "floor_admin_approve_in_budget", "description": "admin with positive in-budget request MUST approveSpend", "type": "floor", "principal_type": "Approver", "action": 'Action::"approveSpend"', "resource_type": "Project", "floor_path": os.path.join(REFS, "floor_admin_approve_in_budget.cedar")},

        # ── Liveness ─────────────────────────────────────────────────────
        {"name": "liveness_request_spend", "description": "at least one requestSpend permitted", "type": "always-denies-liveness", "principal_type": "Approver", "action": 'Action::"requestSpend"', "resource_type": "Project"},
        {"name": "liveness_approve_spend", "description": "at least one approveSpend permitted", "type": "always-denies-liveness", "principal_type": "Approver", "action": 'Action::"approveSpend"', "resource_type": "Project"},
    ]
