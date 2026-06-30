"""Hand-authored verification plan for realworld/approval_chain_workflow.

Exercises Cedar's `set.containsAll()` operator (never tested in any
prior scenario) and state-machine transitions gated on set relations.

The central safety property: finalize is permitted only when
`currentApprovals.containsAll(requiredApprovers)`. A candidate that
accidentally permits finalize without this condition is incorrect, and
the harness must surface the gap.

11 safety + floor checks + 5 liveness = 16 total.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # ── Safety ceilings (one per action) ─────────────────────────────
        {"name": "submit_safety", "description": "submit permitted only when (principal == owner AND status == draft)", "type": "implies", "principal_type": "User", "action": "Action::\"submit\"", "resource_type": "Document", "reference_path": os.path.join(REFS, "submit_safety.cedar")},
        {"name": "approve_safety", "description": "approve permitted only when (principal in requiredApprovers AND status == in_review)", "type": "implies", "principal_type": "User", "action": "Action::\"approve\"", "resource_type": "Document", "reference_path": os.path.join(REFS, "approve_safety.cedar")},
        {"name": "finalize_safety", "description": "finalize permitted only when (principal in requiredApprovers AND status == in_review AND currentApprovals.containsAll(requiredApprovers))", "type": "implies", "principal_type": "User", "action": "Action::\"finalize\"", "resource_type": "Document", "reference_path": os.path.join(REFS, "finalize_safety.cedar")},
        {"name": "reject_safety", "description": "reject permitted only when (principal in requiredApprovers AND status == in_review)", "type": "implies", "principal_type": "User", "action": "Action::\"reject\"", "resource_type": "Document", "reference_path": os.path.join(REFS, "reject_safety.cedar")},
        {"name": "read_safety", "description": "read permitted only when (principal == owner OR principal in requiredApprovers)", "type": "implies", "principal_type": "User", "action": "Action::\"read\"", "resource_type": "Document", "reference_path": os.path.join(REFS, "read_safety.cedar")},

        # ── Floors (positive assertions about what must be permitted) ────
        {"name": "owner_must_submit_draft", "description": "Owner MUST be permitted to submit when status is draft", "type": "floor", "principal_type": "User", "action": "Action::\"submit\"", "resource_type": "Document", "floor_path": os.path.join(REFS, "owner_must_submit_draft.cedar")},
        {"name": "approver_must_approve_in_review", "description": "Required approver MUST be permitted to approve when in_review", "type": "floor", "principal_type": "User", "action": "Action::\"approve\"", "resource_type": "Document", "floor_path": os.path.join(REFS, "approver_must_approve_in_review.cedar")},
        {"name": "approver_must_finalize_when_all_approved", "description": "Required approver MUST be permitted to finalize when ALL required approvers have signed off AND in_review", "type": "floor", "principal_type": "User", "action": "Action::\"finalize\"", "resource_type": "Document", "floor_path": os.path.join(REFS, "approver_must_finalize_when_all_approved.cedar")},
        {"name": "approver_must_reject_in_review", "description": "Required approver MUST be permitted to reject when in_review", "type": "floor", "principal_type": "User", "action": "Action::\"reject\"", "resource_type": "Document", "floor_path": os.path.join(REFS, "approver_must_reject_in_review.cedar")},
        {"name": "owner_must_read_any_state", "description": "Owner MUST be permitted to read in any state", "type": "floor", "principal_type": "User", "action": "Action::\"read\"", "resource_type": "Document", "floor_path": os.path.join(REFS, "owner_must_read_any_state.cedar")},
        {"name": "approver_must_read_any_state", "description": "Required approver MUST be permitted to read in any state", "type": "floor", "principal_type": "User", "action": "Action::\"read\"", "resource_type": "Document", "floor_path": os.path.join(REFS, "approver_must_read_any_state.cedar")},

        # ── Liveness ─────────────────────────────────────────────────────
        {"name": "liveness_submit", "description": "User+submit+Document liveness", "type": "always-denies-liveness", "principal_type": "User", "action": "Action::\"submit\"", "resource_type": "Document"},
        {"name": "liveness_approve", "description": "User+approve+Document liveness", "type": "always-denies-liveness", "principal_type": "User", "action": "Action::\"approve\"", "resource_type": "Document"},
        {"name": "liveness_finalize", "description": "User+finalize+Document liveness", "type": "always-denies-liveness", "principal_type": "User", "action": "Action::\"finalize\"", "resource_type": "Document"},
        {"name": "liveness_reject", "description": "User+reject+Document liveness", "type": "always-denies-liveness", "principal_type": "User", "action": "Action::\"reject\"", "resource_type": "Document"},
        {"name": "liveness_read", "description": "User+read+Document liveness", "type": "always-denies-liveness", "principal_type": "User", "action": "Action::\"read\"", "resource_type": "Document"},
    ]
