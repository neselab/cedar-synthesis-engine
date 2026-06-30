"""Hand-authored verification plan for realworld/loan_approval_workflow.

Multi-tier banking loan approval with numeric approval-limit checks,
role-based action gating, and risk-based escalation. Tests Cedar's
numeric comparison (>=), string equality on roles, boolean guards,
and multi-condition conjunction in the approve ceiling.

The central safety property: approve requires BOTH
`principal.approvalLimit >= resource.amount` AND (for high-risk loans)
`principal.role in {"director", "vp"}`. A candidate that omits either
condition is incorrect.

11 safety/floor checks + 5 liveness = 16 total.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceilings (one per action) ---------------------------------
        {"name": "submit_safety", "description": "submit permitted only when (analyst AND !isSubmitted)", "type": "implies", "principal_type": "Officer", "action": "Action::\"submit\"", "resource_type": "LoanApplication", "reference_path": os.path.join(REFS, "submit_safety.cedar")},
        {"name": "review_safety", "description": "review permitted only when isSubmitted", "type": "implies", "principal_type": "Officer", "action": "Action::\"review\"", "resource_type": "LoanApplication", "reference_path": os.path.join(REFS, "review_safety.cedar")},
        {"name": "approve_safety", "description": "approve permitted only when (isSubmitted AND approvalLimit >= amount AND (not high-risk OR director/vp))", "type": "implies", "principal_type": "Officer", "action": "Action::\"approve\"", "resource_type": "LoanApplication", "reference_path": os.path.join(REFS, "approve_safety.cedar")},
        {"name": "reject_safety", "description": "reject permitted only when isSubmitted", "type": "implies", "principal_type": "Officer", "action": "Action::\"reject\"", "resource_type": "LoanApplication", "reference_path": os.path.join(REFS, "reject_safety.cedar")},
        {"name": "escalate_safety", "description": "escalate permitted only when isSubmitted", "type": "implies", "principal_type": "Officer", "action": "Action::\"escalate\"", "resource_type": "LoanApplication", "reference_path": os.path.join(REFS, "escalate_safety.cedar")},

        # -- Floors (positive assertions about what must be permitted) ---------
        {"name": "analyst_must_submit", "description": "Analyst MUST submit a non-submitted application", "type": "floor", "principal_type": "Officer", "action": "Action::\"submit\"", "resource_type": "LoanApplication", "floor_path": os.path.join(REFS, "analyst_must_submit.cedar")},
        {"name": "any_officer_must_review", "description": "Any officer MUST review a submitted application", "type": "floor", "principal_type": "Officer", "action": "Action::\"review\"", "resource_type": "LoanApplication", "floor_path": os.path.join(REFS, "any_officer_must_review.cedar")},
        {"name": "officer_must_approve_low_risk", "description": "Officer with sufficient limit MUST approve a low-risk submitted application", "type": "floor", "principal_type": "Officer", "action": "Action::\"approve\"", "resource_type": "LoanApplication", "floor_path": os.path.join(REFS, "officer_must_approve_low_risk.cedar")},
        {"name": "director_must_approve_high_risk", "description": "Director with sufficient limit MUST approve a high-risk submitted application", "type": "floor", "principal_type": "Officer", "action": "Action::\"approve\"", "resource_type": "LoanApplication", "floor_path": os.path.join(REFS, "director_must_approve_high_risk.cedar")},
        {"name": "any_officer_must_reject", "description": "Any officer MUST reject a submitted application", "type": "floor", "principal_type": "Officer", "action": "Action::\"reject\"", "resource_type": "LoanApplication", "floor_path": os.path.join(REFS, "any_officer_must_reject.cedar")},
        {"name": "any_officer_must_escalate", "description": "Any officer MUST escalate a submitted application", "type": "floor", "principal_type": "Officer", "action": "Action::\"escalate\"", "resource_type": "LoanApplication", "floor_path": os.path.join(REFS, "any_officer_must_escalate.cedar")},

        # -- Liveness ---------------------------------------------------------
        {"name": "liveness_submit", "description": "Officer+submit+LoanApplication liveness", "type": "always-denies-liveness", "principal_type": "Officer", "action": "Action::\"submit\"", "resource_type": "LoanApplication"},
        {"name": "liveness_review", "description": "Officer+review+LoanApplication liveness", "type": "always-denies-liveness", "principal_type": "Officer", "action": "Action::\"review\"", "resource_type": "LoanApplication"},
        {"name": "liveness_approve", "description": "Officer+approve+LoanApplication liveness", "type": "always-denies-liveness", "principal_type": "Officer", "action": "Action::\"approve\"", "resource_type": "LoanApplication"},
        {"name": "liveness_reject", "description": "Officer+reject+LoanApplication liveness", "type": "always-denies-liveness", "principal_type": "Officer", "action": "Action::\"reject\"", "resource_type": "LoanApplication"},
        {"name": "liveness_escalate", "description": "Officer+escalate+LoanApplication liveness", "type": "always-denies-liveness", "principal_type": "Officer", "action": "Action::\"escalate\"", "resource_type": "LoanApplication"},
    ]
