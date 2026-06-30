"""Hand-authored verification plan for realworld/audit_log_immutability.

Append-only audit log: services write, analysts/auditors/admins read,
delete and modify are unconditionally forbidden. Tests asymmetric
action permissions and the forbid-all pattern for immutability.

Note: delete and modify use "implies" ceilings with an EMPTY reference
(a policy that permits nothing). This encodes "no one should ever be
permitted to delete/modify" — if the candidate permits delete for
anyone, symcc will find a counterexample.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # ── Safety ceilings ──────────────────────────────────────────────
        {"name": "append_safety", "description": "append only when service", "type": "implies", "principal_type": "User", "action": 'Action::"append"', "resource_type": "AuditEntry", "reference_path": os.path.join(REFS, "append_safety.cedar")},
        {"name": "read_safety", "description": "read only when analyst/auditor/admin", "type": "implies", "principal_type": "User", "action": 'Action::"read"', "resource_type": "AuditEntry", "reference_path": os.path.join(REFS, "read_safety.cedar")},
        {"name": "export_safety", "description": "export only when auditor", "type": "implies", "principal_type": "User", "action": 'Action::"export"', "resource_type": "AuditEntry", "reference_path": os.path.join(REFS, "export_safety.cedar")},

        # ── Floors ───────────────────────────────────────────────────────
        {"name": "floor_service_append", "description": "service MUST append", "type": "floor", "principal_type": "User", "action": 'Action::"append"', "resource_type": "AuditEntry", "floor_path": os.path.join(REFS, "floor_service_append.cedar")},
        {"name": "floor_analyst_read", "description": "analyst MUST read", "type": "floor", "principal_type": "User", "action": 'Action::"read"', "resource_type": "AuditEntry", "floor_path": os.path.join(REFS, "floor_analyst_read.cedar")},
        {"name": "floor_auditor_export", "description": "auditor MUST export", "type": "floor", "principal_type": "User", "action": 'Action::"export"', "resource_type": "AuditEntry", "floor_path": os.path.join(REFS, "floor_auditor_export.cedar")},

        # ── Liveness ─────────────────────────────────────────────────────
        {"name": "liveness_append", "description": "at least one append permitted", "type": "always-denies-liveness", "principal_type": "User", "action": 'Action::"append"', "resource_type": "AuditEntry"},
        {"name": "liveness_read", "description": "at least one read permitted", "type": "always-denies-liveness", "principal_type": "User", "action": 'Action::"read"', "resource_type": "AuditEntry"},
        {"name": "liveness_export", "description": "at least one export permitted", "type": "always-denies-liveness", "principal_type": "User", "action": 'Action::"export"', "resource_type": "AuditEntry"},
    ]
