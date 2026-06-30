"""Verification plan for realworld/hundred_tenant_isolation.

102 checks total:
  - 1 ceiling: candidate ⇒ tenant_equality_ceiling (no over-permissive
    policy may grant cross-tenant access).
  - 100 floors: one per tenant, candidate ⇐ must_access_tenant_<i>
    (every legitimate same-tenant request must be permitted).
  - 1 liveness: at least one (User, Resource) request must be permitted.

The plan is generated programmatically from the integer range [0, 100)
to match the reference files written by the inline generator. Adding
more tenants is a one-line change.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")
N_TENANTS = 100


def get_checks():
    checks = []

    # ── Ceiling: tenant-id equality bound on every permit ─────────
    checks.append({
        "name": "tenant_equality_ceiling",
        "description": "access permitted only when principal.tenantId == resource.tenantId",
        "type": "implies",
        "principal_type": "User",
        "action": "Action::\"access\"",
        "resource_type": "Resource",
        "reference_path": os.path.join(REFS, "tenant_equality_ceiling.cedar"),
    })

    # ── 100 per-tenant floors ─────────────────────────────────────
    for i in range(N_TENANTS):
        tid = f"tenant_{i}"
        checks.append({
            "name": f"must_access_{tid}",
            "description": f"a user from {tid} MUST access a resource from {tid}",
            "type": "floor",
            "principal_type": "User",
            "action": "Action::\"access\"",
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, f"must_access_{tid}.cedar"),
        })

    # ── Liveness: policy is not vacuously forbid-everything ───────
    checks.append({
        "name": "liveness_access",
        "description": "access has at least one permitted request",
        "type": "always-denies-liveness",
        "principal_type": "User",
        "action": "Action::\"access\"",
        "resource_type": "Resource",
    })

    return checks
