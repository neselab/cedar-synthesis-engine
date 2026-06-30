"""Hand-authored verification plan for realworld/default_scope_mismatch.

Tests the interaction between an implicit/explicit default at one scope
(tenant.defaultDeny) and an explicit override at another scope (the
user-level admin role). Cross-tenant access is an unconditional gate
that no override may bypass; tenant default-deny is overridable by the
admin role; write is additionally restricted to admins regardless of
the tenant flag.

Common failure mode: encoding the cross-tenant gate as conditional on
the admin role (e.g. forbid cross-tenant unless admin), which would let
a tenant admin read documents in OTHER tenants — a serious isolation
bug. The read_safety / write_safety ceilings catch that. A second
failure mode is forgetting that write requires admin even in a
default-allow tenant — caught by write_safety.

8 checks total (2 ceilings + 4 floors + 2 liveness).
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # ── Safety ceilings ──────────────────────────────────────────────
        {
            "name": "read_safety",
            "description": "read permitted only when same-tenant AND (tenant !defaultDeny OR principal is admin); cross-tenant is unconditionally denied",
            "type": "implies",
            "principal_type": "User",
            "action": "Action::\"read\"",
            "resource_type": "Document",
            "reference_path": os.path.join(REFS, "read_safety.cedar"),
        },
        {
            "name": "write_safety",
            "description": "write permitted only when same-tenant AND principal is admin; cross-tenant is unconditionally denied and members never write",
            "type": "implies",
            "principal_type": "User",
            "action": "Action::\"write\"",
            "resource_type": "Document",
            "reference_path": os.path.join(REFS, "write_safety.cedar"),
        },

        # ── Floors (positive assertions) ─────────────────────────────────
        {
            "name": "same_tenant_member_default_allow_read_must_permit",
            "description": "A member MUST be permitted to read a same-tenant document when the tenant is not in default-deny mode",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"read\"",
            "resource_type": "Document",
            "floor_path": os.path.join(REFS, "same_tenant_member_default_allow_read.cedar"),
        },
        {
            "name": "same_tenant_admin_default_deny_read_must_permit",
            "description": "A tenant admin MUST be permitted to read a same-tenant document EVEN WHEN the tenant is in default-deny mode (user-scope override of tenant default)",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"read\"",
            "resource_type": "Document",
            "floor_path": os.path.join(REFS, "same_tenant_admin_default_deny_read.cedar"),
        },
        {
            "name": "same_tenant_admin_default_allow_write_must_permit",
            "description": "A tenant admin MUST be permitted to write a same-tenant document when the tenant is not in default-deny mode",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"write\"",
            "resource_type": "Document",
            "floor_path": os.path.join(REFS, "same_tenant_admin_default_allow_write.cedar"),
        },
        {
            "name": "same_tenant_admin_default_deny_write_must_permit",
            "description": "A tenant admin MUST be permitted to write a same-tenant document EVEN WHEN the tenant is in default-deny mode",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"write\"",
            "resource_type": "Document",
            "floor_path": os.path.join(REFS, "same_tenant_admin_default_deny_write.cedar"),
        },

        # ── Liveness ─────────────────────────────────────────────────────
        {
            "name": "liveness_read",
            "description": "User+read+Document liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": "Action::\"read\"",
            "resource_type": "Document",
        },
        {
            "name": "liveness_write",
            "description": "User+write+Document liveness",
            "type": "always-denies-liveness",
            "principal_type": "User",
            "action": "Action::\"write\"",
            "resource_type": "Document",
        },
    ]
