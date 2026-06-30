"""Hand-authored verification plan for realworld/context_scoped_admin.

Tests that admin powers are scoped to specific tenants via an explicit
adminOf set, and do NOT leak across tenant boundaries based on a role
string.

The trap: a user with role == "admin" but resource.tenant NOT in
principal.adminOf must be DENIED. The candidate must NOT use the role
string as a gate — only the adminOf set membership is the source of
truth.

10 checks total (3 ceilings + 4 floors + 3 liveness).
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # ── Safety ceilings ──────────────────────────────────────────────
        {"name": "view_safety", "description": "view permitted only when resource.tenant is in principal.adminOf (no cross-tenant view)", "type": "implies", "principal_type": "User", "action": "Action::\"view\"", "resource_type": "Resource", "reference_path": os.path.join(REFS, "view_safety.cedar")},
        {"name": "modify_safety", "description": "modify permitted only when resource.tenant is in principal.adminOf (no cross-tenant modify)", "type": "implies", "principal_type": "User", "action": "Action::\"modify\"", "resource_type": "Resource", "reference_path": os.path.join(REFS, "modify_safety.cedar")},
        {"name": "delete_safety", "description": "delete permitted only when resource.tenant is in principal.adminOf (no cross-tenant delete)", "type": "implies", "principal_type": "User", "action": "Action::\"delete\"", "resource_type": "Resource", "reference_path": os.path.join(REFS, "delete_safety.cedar")},

        # ── Floors (positive assertions) ─────────────────────────────────
        {"name": "scoped_admin_view_must_permit", "description": "User whose adminOf includes resource.tenant MUST be permitted to view", "type": "floor", "principal_type": "User", "action": "Action::\"view\"", "resource_type": "Resource", "floor_path": os.path.join(REFS, "scoped_admin_view_must_permit.cedar")},
        {"name": "scoped_admin_modify_must_permit", "description": "User whose adminOf includes resource.tenant MUST be permitted to modify", "type": "floor", "principal_type": "User", "action": "Action::\"modify\"", "resource_type": "Resource", "floor_path": os.path.join(REFS, "scoped_admin_modify_must_permit.cedar")},
        {"name": "scoped_admin_delete_must_permit", "description": "User whose adminOf includes resource.tenant MUST be permitted to delete", "type": "floor", "principal_type": "User", "action": "Action::\"delete\"", "resource_type": "Resource", "floor_path": os.path.join(REFS, "scoped_admin_delete_must_permit.cedar")},
        {"name": "scoped_admin_view_role_independent", "description": "User with role=='viewer' but adminOf includes resource.tenant MUST be permitted to view (role string is not the gate)", "type": "floor", "principal_type": "User", "action": "Action::\"view\"", "resource_type": "Resource", "floor_path": os.path.join(REFS, "scoped_admin_view_role_independent.cedar")},

        # ── Liveness ─────────────────────────────────────────────────────
        {"name": "liveness_view", "description": "User+view+Resource liveness", "type": "always-denies-liveness", "principal_type": "User", "action": "Action::\"view\"", "resource_type": "Resource"},
        {"name": "liveness_modify", "description": "User+modify+Resource liveness", "type": "always-denies-liveness", "principal_type": "User", "action": "Action::\"modify\"", "resource_type": "Resource"},
        {"name": "liveness_delete", "description": "User+delete+Resource liveness", "type": "always-denies-liveness", "principal_type": "User", "action": "Action::\"delete\"", "resource_type": "Resource"},
    ]
