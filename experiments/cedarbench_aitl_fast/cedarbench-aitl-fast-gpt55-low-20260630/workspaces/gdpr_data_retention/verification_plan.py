"""Hand-authored verification plan for realworld/gdpr_data_retention.

GDPR data retention with right-to-erasure. Tests datetime comparisons
for retention expiry, boolean flags for erasure requests, and
role-based access with DPO compliance override.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # ── Safety ceilings ──────────────────────────────────────────────
        {"name": "read_safety", "description": "read only when active record AND authorized role", "type": "implies", "principal_type": "User", "action": 'Action::"read"', "resource_type": "DataRecord", "reference_path": os.path.join(REFS, "read_safety.cedar")},
        {"name": "process_safety", "description": "process only when processor AND active record", "type": "implies", "principal_type": "User", "action": 'Action::"process"', "resource_type": "DataRecord", "reference_path": os.path.join(REFS, "process_safety.cedar")},
        {"name": "delete_safety", "description": "delete only when controller or dpo", "type": "implies", "principal_type": "User", "action": 'Action::"delete"', "resource_type": "DataRecord", "reference_path": os.path.join(REFS, "delete_safety.cedar")},
        {"name": "audit_safety", "description": "audit only when dpo", "type": "implies", "principal_type": "User", "action": 'Action::"audit"', "resource_type": "DataRecord", "reference_path": os.path.join(REFS, "audit_safety.cedar")},

        # ── Floors ───────────────────────────────────────────────────────
        {"name": "floor_processor_read_active", "description": "processor MUST read active records", "type": "floor", "principal_type": "User", "action": 'Action::"read"', "resource_type": "DataRecord", "floor_path": os.path.join(REFS, "floor_processor_read_active.cedar")},
        {"name": "floor_processor_process_active", "description": "processor MUST process active records", "type": "floor", "principal_type": "User", "action": 'Action::"process"', "resource_type": "DataRecord", "floor_path": os.path.join(REFS, "floor_processor_process_active.cedar")},
        {"name": "floor_controller_delete", "description": "controller MUST delete any record", "type": "floor", "principal_type": "User", "action": 'Action::"delete"', "resource_type": "DataRecord", "floor_path": os.path.join(REFS, "floor_controller_delete.cedar")},
        {"name": "floor_dpo_audit", "description": "dpo MUST audit any record", "type": "floor", "principal_type": "User", "action": 'Action::"audit"', "resource_type": "DataRecord", "floor_path": os.path.join(REFS, "floor_dpo_audit.cedar")},

        # ── Liveness ─────────────────────────────────────────────────────
        {"name": "liveness_read", "description": "at least one read permitted", "type": "always-denies-liveness", "principal_type": "User", "action": 'Action::"read"', "resource_type": "DataRecord"},
        {"name": "liveness_process", "description": "at least one process permitted", "type": "always-denies-liveness", "principal_type": "User", "action": 'Action::"process"', "resource_type": "DataRecord"},
        {"name": "liveness_delete", "description": "at least one delete permitted", "type": "always-denies-liveness", "principal_type": "User", "action": 'Action::"delete"', "resource_type": "DataRecord"},
        {"name": "liveness_audit", "description": "at least one audit permitted", "type": "always-denies-liveness", "principal_type": "User", "action": 'Action::"audit"', "resource_type": "DataRecord"},
    ]
