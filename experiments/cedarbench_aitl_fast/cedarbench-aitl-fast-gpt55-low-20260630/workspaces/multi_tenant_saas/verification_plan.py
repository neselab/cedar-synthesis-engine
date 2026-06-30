"""Hand-authored verification plan for realworld/multi_tenant_saas.

Fundamental SaaS tenant-isolation pattern. The key safety properties:
  - Reads are restricted to the same tenant, plus a narrow cross-tenant
    path for global support with an active session and ticket reference.
  - Writes and deletes are ALWAYS same-tenant only, regardless of
    global-support status.

The common failure mode this scenario hunts: the candidate accidentally
extends global-support cross-tenant access to writes or deletes. The
edit_safety / delete_safety ceilings will catch that.

10 checks total (3 ceilings + 4 floors + 3 liveness).
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # ── Safety ceilings ──────────────────────────────────────────────
        {"name": "read_safety", "description": "readResource permitted only when (same tenant OR (global support AND session active AND ticket non-empty))", "type": "implies", "principal_type": "User", "action": "Action::\"readResource\"", "resource_type": "Resource", "reference_path": os.path.join(REFS, "read_safety.cedar")},
        {"name": "write_safety", "description": "writeResource permitted only when same tenant (no cross-tenant writes)", "type": "implies", "principal_type": "User", "action": "Action::\"writeResource\"", "resource_type": "Resource", "reference_path": os.path.join(REFS, "write_safety.cedar")},
        {"name": "delete_safety", "description": "deleteResource permitted only when same tenant (no cross-tenant deletes)", "type": "implies", "principal_type": "User", "action": "Action::\"deleteResource\"", "resource_type": "Resource", "reference_path": os.path.join(REFS, "delete_safety.cedar")},

        # ── Floors (positive assertions) ─────────────────────────────────
        {"name": "same_tenant_read_must_permit", "description": "User MUST read a resource in the same tenant", "type": "floor", "principal_type": "User", "action": "Action::\"readResource\"", "resource_type": "Resource", "floor_path": os.path.join(REFS, "same_tenant_read_must_permit.cedar")},
        {"name": "same_tenant_write_must_permit", "description": "User MUST write a resource in the same tenant", "type": "floor", "principal_type": "User", "action": "Action::\"writeResource\"", "resource_type": "Resource", "floor_path": os.path.join(REFS, "same_tenant_write_must_permit.cedar")},
        {"name": "same_tenant_delete_must_permit", "description": "User MUST delete a resource in the same tenant", "type": "floor", "principal_type": "User", "action": "Action::\"deleteResource\"", "resource_type": "Resource", "floor_path": os.path.join(REFS, "same_tenant_delete_must_permit.cedar")},
        {"name": "global_support_cross_tenant_read_must_permit", "description": "Global-support user with active session AND ticketId MUST read a cross-tenant resource", "type": "floor", "principal_type": "User", "action": "Action::\"readResource\"", "resource_type": "Resource", "floor_path": os.path.join(REFS, "global_support_cross_tenant_read_must_permit.cedar")},

        # ── Liveness ─────────────────────────────────────────────────────
        {"name": "liveness_read_resource", "description": "User+readResource+Resource liveness", "type": "always-denies-liveness", "principal_type": "User", "action": "Action::\"readResource\"", "resource_type": "Resource"},
        {"name": "liveness_write_resource", "description": "User+writeResource+Resource liveness", "type": "always-denies-liveness", "principal_type": "User", "action": "Action::\"writeResource\"", "resource_type": "Resource"},
        {"name": "liveness_delete_resource", "description": "User+deleteResource+Resource liveness", "type": "always-denies-liveness", "principal_type": "User", "action": "Action::\"deleteResource\"", "resource_type": "Resource"},
    ]
