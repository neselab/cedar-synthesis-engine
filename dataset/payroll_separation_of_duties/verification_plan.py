"""Hand-authored verification plan for realworld/payroll_separation_of_duties.

SOX-grade Separation of Duties: the user who initiated a payroll entry
cannot approve it. Additional rules: role-based action assignment,
amount-threshold escalation (CFO-only for large entries), state
machine gating.

The central safety property is `principal != resource.initiator` on
approve. A candidate that forgets this check breaks the fundamental
SoD invariant and fails approve_safety.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # ── Safety ceilings ──────────────────────────────────────────────
        {"name": "initiate_safety", "description": "initiate permitted only when (clerk AND draft)", "type": "implies", "principal_type": "User", "action": "Action::\"initiate\"", "resource_type": "PayrollEntry", "reference_path": os.path.join(REFS, "initiate_safety.cedar")},
        {"name": "approve_safety", "description": "approve permitted only when (manager/cfo AND pending_approval AND != initiator AND (amount<50k OR cfo))", "type": "implies", "principal_type": "User", "action": "Action::\"approve\"", "resource_type": "PayrollEntry", "reference_path": os.path.join(REFS, "approve_safety.cedar")},
        {"name": "release_safety", "description": "release permitted only when (cfo AND approved)", "type": "implies", "principal_type": "User", "action": "Action::\"release\"", "resource_type": "PayrollEntry", "reference_path": os.path.join(REFS, "release_safety.cedar")},
        {"name": "reject_safety", "description": "reject permitted only when (manager/cfo AND pending_approval)", "type": "implies", "principal_type": "User", "action": "Action::\"reject\"", "resource_type": "PayrollEntry", "reference_path": os.path.join(REFS, "reject_safety.cedar")},
        {"name": "read_safety", "description": "read permitted unconditionally", "type": "implies", "principal_type": "User", "action": "Action::\"read\"", "resource_type": "PayrollEntry", "reference_path": os.path.join(REFS, "read_safety.cedar")},

        # ── Floors ───────────────────────────────────────────────────────
        {"name": "clerk_must_initiate_draft", "description": "Clerk MUST initiate a draft entry", "type": "floor", "principal_type": "User", "action": "Action::\"initiate\"", "resource_type": "PayrollEntry", "floor_path": os.path.join(REFS, "clerk_must_initiate_draft.cedar")},
        {"name": "manager_non_initiator_must_approve_small", "description": "Manager (not initiator) MUST approve a small pending entry", "type": "floor", "principal_type": "User", "action": "Action::\"approve\"", "resource_type": "PayrollEntry", "floor_path": os.path.join(REFS, "manager_non_initiator_must_approve_small.cedar")},
        {"name": "cfo_non_initiator_must_approve_large", "description": "CFO (not initiator) MUST approve a large pending entry", "type": "floor", "principal_type": "User", "action": "Action::\"approve\"", "resource_type": "PayrollEntry", "floor_path": os.path.join(REFS, "cfo_non_initiator_must_approve_large.cedar")},
        {"name": "cfo_must_release_approved", "description": "CFO MUST release an approved entry", "type": "floor", "principal_type": "User", "action": "Action::\"release\"", "resource_type": "PayrollEntry", "floor_path": os.path.join(REFS, "cfo_must_release_approved.cedar")},
        {"name": "any_user_must_read", "description": "Any user MUST read any entry", "type": "floor", "principal_type": "User", "action": "Action::\"read\"", "resource_type": "PayrollEntry", "floor_path": os.path.join(REFS, "any_user_must_read.cedar")},

        # ── Liveness ─────────────────────────────────────────────────────
        {"name": "liveness_initiate", "description": "User+initiate+PayrollEntry liveness", "type": "always-denies-liveness", "principal_type": "User", "action": "Action::\"initiate\"", "resource_type": "PayrollEntry"},
        {"name": "liveness_approve", "description": "User+approve+PayrollEntry liveness", "type": "always-denies-liveness", "principal_type": "User", "action": "Action::\"approve\"", "resource_type": "PayrollEntry"},
        {"name": "liveness_release", "description": "User+release+PayrollEntry liveness", "type": "always-denies-liveness", "principal_type": "User", "action": "Action::\"release\"", "resource_type": "PayrollEntry"},
        {"name": "liveness_reject", "description": "User+reject+PayrollEntry liveness", "type": "always-denies-liveness", "principal_type": "User", "action": "Action::\"reject\"", "resource_type": "PayrollEntry"},
        {"name": "liveness_read", "description": "User+read+PayrollEntry liveness", "type": "always-denies-liveness", "principal_type": "User", "action": "Action::\"read\"", "resource_type": "PayrollEntry"},
    ]
