"""Hand-authored verification plan for realworld/resource_budget_enforcement.

Quota-based resource provisioning with tier-derived limits.
Tests numeric comparison on context-provided usage counters.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # ── Safety ceilings ──────────────────────────────────────────────
        {"name": "create_safety", "description": "create only within budget per tier", "type": "implies", "principal_type": "Tenant", "action": 'Action::"create"', "resource_type": "Resource", "reference_path": os.path.join(REFS, "create_safety.cedar")},
        {"name": "read_safety", "description": "any tenant can read", "type": "implies", "principal_type": "Tenant", "action": 'Action::"read"', "resource_type": "Resource", "reference_path": os.path.join(REFS, "read_safety.cedar")},
        {"name": "delete_safety", "description": "any tenant can delete", "type": "implies", "principal_type": "Tenant", "action": 'Action::"delete"', "resource_type": "Resource", "reference_path": os.path.join(REFS, "delete_safety.cedar")},
        {"name": "upgrade_safety", "description": "upgrade only when pro or enterprise", "type": "implies", "principal_type": "Tenant", "action": 'Action::"upgrade"', "resource_type": "Resource", "reference_path": os.path.join(REFS, "upgrade_safety.cedar")},

        # ── Floors ───────────────────────────────────────────────────────
        {"name": "floor_free_create_under_limit", "description": "free tenant with <5 resources MUST create", "type": "floor", "principal_type": "Tenant", "action": 'Action::"create"', "resource_type": "Resource", "floor_path": os.path.join(REFS, "floor_free_create_under_limit.cedar")},
        {"name": "floor_enterprise_create", "description": "enterprise tenant MUST always create", "type": "floor", "principal_type": "Tenant", "action": 'Action::"create"', "resource_type": "Resource", "floor_path": os.path.join(REFS, "floor_enterprise_create.cedar")},
        {"name": "floor_any_read", "description": "any tenant MUST read", "type": "floor", "principal_type": "Tenant", "action": 'Action::"read"', "resource_type": "Resource", "floor_path": os.path.join(REFS, "floor_any_read.cedar")},
        {"name": "floor_pro_upgrade", "description": "pro tenant MUST upgrade", "type": "floor", "principal_type": "Tenant", "action": 'Action::"upgrade"', "resource_type": "Resource", "floor_path": os.path.join(REFS, "floor_pro_upgrade.cedar")},

        # ── Liveness ─────────────────────────────────────────────────────
        {"name": "liveness_create", "description": "at least one create permitted", "type": "always-denies-liveness", "principal_type": "Tenant", "action": 'Action::"create"', "resource_type": "Resource"},
        {"name": "liveness_read", "description": "at least one read permitted", "type": "always-denies-liveness", "principal_type": "Tenant", "action": 'Action::"read"', "resource_type": "Resource"},
        {"name": "liveness_delete", "description": "at least one delete permitted", "type": "always-denies-liveness", "principal_type": "Tenant", "action": 'Action::"delete"', "resource_type": "Resource"},
        {"name": "liveness_upgrade", "description": "at least one upgrade permitted", "type": "always-denies-liveness", "principal_type": "Tenant", "action": 'Action::"upgrade"', "resource_type": "Resource"},
    ]
