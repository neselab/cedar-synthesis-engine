"""Verification plan for realworld/backup_restore_asymmetric.
Asymmetric backup (easy) vs restore (restricted) with environment gates.
"""
import os
REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")

def get_checks():
    return [
        {"name": "backup_safety", "description": "backup only when engineer/sre/admin", "type": "implies", "principal_type": "Operator", "action": 'Action::"backup"', "resource_type": "System", "reference_path": os.path.join(REFS, "backup_safety.cedar")},
        {"name": "restore_safety", "description": "restore only when sre/admin with env gate", "type": "implies", "principal_type": "Operator", "action": 'Action::"restore"', "resource_type": "System", "reference_path": os.path.join(REFS, "restore_safety.cedar")},
        {"name": "verify_safety", "description": "verify only when engineer/sre/admin", "type": "implies", "principal_type": "Operator", "action": 'Action::"verify"', "resource_type": "System", "reference_path": os.path.join(REFS, "verify_safety.cedar")},
        {"name": "floor_engineer_backup", "description": "engineer MUST backup", "type": "floor", "principal_type": "Operator", "action": 'Action::"backup"', "resource_type": "System", "floor_path": os.path.join(REFS, "floor_engineer_backup.cedar")},
        {"name": "floor_sre_restore_staging", "description": "sre MUST restore staging", "type": "floor", "principal_type": "Operator", "action": 'Action::"restore"', "resource_type": "System", "floor_path": os.path.join(REFS, "floor_sre_restore_staging.cedar")},
        {"name": "floor_oncall_sre_restore_prod", "description": "on-call sre MUST restore production", "type": "floor", "principal_type": "Operator", "action": 'Action::"restore"', "resource_type": "System", "floor_path": os.path.join(REFS, "floor_oncall_sre_restore_prod.cedar")},
        {"name": "floor_admin_restore_prod", "description": "admin MUST restore production", "type": "floor", "principal_type": "Operator", "action": 'Action::"restore"', "resource_type": "System", "floor_path": os.path.join(REFS, "floor_admin_restore_prod.cedar")},
        {"name": "liveness_backup", "description": "at least one backup permitted", "type": "always-denies-liveness", "principal_type": "Operator", "action": 'Action::"backup"', "resource_type": "System"},
        {"name": "liveness_restore", "description": "at least one restore permitted", "type": "always-denies-liveness", "principal_type": "Operator", "action": 'Action::"restore"', "resource_type": "System"},
        {"name": "liveness_verify", "description": "at least one verify permitted", "type": "always-denies-liveness", "principal_type": "Operator", "action": 'Action::"verify"', "resource_type": "System"},
    ]
