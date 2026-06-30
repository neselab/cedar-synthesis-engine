"""Hand-authored verification plan for realworld/five_way_role_intersection.

§8.6 role-intersection trap stress test scaled to 5 roles × 5 actions
with multi-role principals (primary role + secondaryRoles set).

The common failure mode this scenario hunts: the candidate tries to
encode "role X is blocked from action Y" using a forbid rule keyed on
principal.role, which incorrectly blocks a user who is both X AND
another role Z whose permit covers Y. The correct pattern is per-role
permits with role membership defined as
  principal.role == R || principal.secondaryRoles.contains(R).

5 ceilings (one per action) + 7 floors (diverse role×action×category
coverage, including both ends of the escalation chain) + 5 liveness =
17 checks total.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # ── Safety ceilings: one per action ────────────────────────────────
        {"name": "read_ceiling", "description": "read is permitted only per the per-role, per-category grid (admin/auditor any; developer code+logs; qa code+tickets; support tickets)", "type": "implies", "principal_type": "User", "action": "Action::\"read\"", "resource_type": "Resource", "reference_path": os.path.join(REFS, "read_ceiling.cedar")},
        {"name": "modify_ceiling", "description": "modify is permitted only for admin (any), developer (code+config), or qa (tickets)", "type": "implies", "principal_type": "User", "action": "Action::\"modify\"", "resource_type": "Resource", "reference_path": os.path.join(REFS, "modify_ceiling.cedar")},
        {"name": "delete_ceiling", "description": "delete is permitted only when the principal holds the admin role (primary or secondary)", "type": "implies", "principal_type": "User", "action": "Action::\"delete\"", "resource_type": "Resource", "reference_path": os.path.join(REFS, "delete_ceiling.cedar")},
        {"name": "audit_ceiling", "description": "audit is permitted only for auditor (any) or developer (logs only)", "type": "implies", "principal_type": "User", "action": "Action::\"audit\"", "resource_type": "Resource", "reference_path": os.path.join(REFS, "audit_ceiling.cedar")},
        {"name": "escalate_ceiling", "description": "escalate is permitted only when the principal holds support, qa, or developer (admin is top of chain; auditor is off-chain)", "type": "implies", "principal_type": "User", "action": "Action::\"escalate\"", "resource_type": "Resource", "reference_path": os.path.join(REFS, "escalate_ceiling.cedar")},

        # ── Floors (positive per-role assertions) ──────────────────────────
        {"name": "floor_admin_delete", "description": "admin (primary OR secondary) MUST be permitted to delete any resource", "type": "floor", "principal_type": "User", "action": "Action::\"delete\"", "resource_type": "Resource", "floor_path": os.path.join(REFS, "floor_admin_delete.cedar")},
        {"name": "floor_developer_read_code", "description": "developer MUST be permitted to read a code resource", "type": "floor", "principal_type": "User", "action": "Action::\"read\"", "resource_type": "Resource", "floor_path": os.path.join(REFS, "floor_developer_read_code.cedar")},
        {"name": "floor_support_read_tickets", "description": "support MUST be permitted to read a tickets resource", "type": "floor", "principal_type": "User", "action": "Action::\"read\"", "resource_type": "Resource", "floor_path": os.path.join(REFS, "floor_support_read_tickets.cedar")},
        {"name": "floor_qa_modify_tickets", "description": "qa MUST be permitted to modify a tickets resource", "type": "floor", "principal_type": "User", "action": "Action::\"modify\"", "resource_type": "Resource", "floor_path": os.path.join(REFS, "floor_qa_modify_tickets.cedar")},
        {"name": "floor_auditor_audit_logs", "description": "auditor MUST be permitted to audit a logs resource", "type": "floor", "principal_type": "User", "action": "Action::\"audit\"", "resource_type": "Resource", "floor_path": os.path.join(REFS, "floor_auditor_audit_logs.cedar")},
        {"name": "floor_support_escalate", "description": "support MUST be permitted to escalate (first link in chain)", "type": "floor", "principal_type": "User", "action": "Action::\"escalate\"", "resource_type": "Resource", "floor_path": os.path.join(REFS, "floor_support_escalate.cedar")},
        {"name": "floor_developer_escalate", "description": "developer MUST be permitted to escalate (third link in chain)", "type": "floor", "principal_type": "User", "action": "Action::\"escalate\"", "resource_type": "Resource", "floor_path": os.path.join(REFS, "floor_developer_escalate.cedar")},

        # ── Liveness: one per action ───────────────────────────────────────
        {"name": "liveness_read", "description": "User+read+Resource liveness", "type": "always-denies-liveness", "principal_type": "User", "action": "Action::\"read\"", "resource_type": "Resource"},
        {"name": "liveness_modify", "description": "User+modify+Resource liveness", "type": "always-denies-liveness", "principal_type": "User", "action": "Action::\"modify\"", "resource_type": "Resource"},
        {"name": "liveness_delete", "description": "User+delete+Resource liveness", "type": "always-denies-liveness", "principal_type": "User", "action": "Action::\"delete\"", "resource_type": "Resource"},
        {"name": "liveness_audit", "description": "User+audit+Resource liveness", "type": "always-denies-liveness", "principal_type": "User", "action": "Action::\"audit\"", "resource_type": "Resource"},
        {"name": "liveness_escalate", "description": "User+escalate+Resource liveness", "type": "always-denies-liveness", "principal_type": "User", "action": "Action::\"escalate\"", "resource_type": "Resource"},
    ]
