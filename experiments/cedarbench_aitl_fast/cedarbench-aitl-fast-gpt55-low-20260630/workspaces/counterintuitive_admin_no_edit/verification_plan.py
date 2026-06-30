"""Hand-authored verification plan for realworld/counterintuitive_admin_no_edit.

Counterintuitive RBAC: the `auditAdmin` role has the BROADEST view access
but ZERO write power. This deliberately violates the "admin = superset"
prior that small models default to.

Tests:
  - That Phase 2 resists the RBAC prior and produces an `edit`/`delete`
    permit that EXCLUDES `auditAdmin`.
  - That `auditAdmin` is preserved as a permitted view role (broad VIEW
    is the audit role's defining capability — failing to include it would
    break the auditAdmin_must_view floor).
  - That manager retains the only delete privilege.

Hunts for failure modes:
  - Adding `principal.role == "auditAdmin"` to the `edit` permit
    (RBAC prior collapse).
  - Adding `principal.role == "auditAdmin"` to the `delete` permit
    (same prior, on the most destructive action).
  - Allowing `editor` to delete (over-generalization across actions).
  - Forgetting auditAdmin's view permit (overcorrection after the
    write-exclusion realization).

Per §8.6, the auditAdmin write-prohibition is encoded as POSITIVE PERMITS
that simply do not enumerate auditAdmin (no `forbid when role ==
"auditAdmin"` policy).
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceilings ------------------------------------------------
        {
            "name": "view_safety",
            "description": "view permitted only for editor, manager, or auditAdmin",
            "type": "implies",
            "principal_type": "Worker",
            "action": 'Action::"view"',
            "resource_type": "Record",
            "reference_path": os.path.join(REFS, "view_safety.cedar"),
        },
        {
            "name": "edit_safety",
            "description": "edit permitted only for editor or manager (NOT auditAdmin — counterintuitive)",
            "type": "implies",
            "principal_type": "Worker",
            "action": 'Action::"edit"',
            "resource_type": "Record",
            "reference_path": os.path.join(REFS, "edit_safety.cedar"),
        },
        {
            "name": "delete_safety",
            "description": "delete permitted only for manager (NOT editor, NOT auditAdmin)",
            "type": "implies",
            "principal_type": "Worker",
            "action": 'Action::"delete"',
            "resource_type": "Record",
            "reference_path": os.path.join(REFS, "delete_safety.cedar"),
        },

        # -- Floors ---------------------------------------------------------
        {
            "name": "auditAdmin_must_view",
            "description": "auditAdmin MUST be permitted to view any Record (counterintuitive but load-bearing)",
            "type": "floor",
            "principal_type": "Worker",
            "action": 'Action::"view"',
            "resource_type": "Record",
            "floor_path": os.path.join(REFS, "auditAdmin_must_view.cedar"),
        },
        {
            "name": "editor_must_edit",
            "description": "editor MUST be permitted to edit any Record",
            "type": "floor",
            "principal_type": "Worker",
            "action": 'Action::"edit"',
            "resource_type": "Record",
            "floor_path": os.path.join(REFS, "editor_must_edit.cedar"),
        },
        {
            "name": "manager_must_edit",
            "description": "manager MUST be permitted to edit any Record",
            "type": "floor",
            "principal_type": "Worker",
            "action": 'Action::"edit"',
            "resource_type": "Record",
            "floor_path": os.path.join(REFS, "manager_must_edit.cedar"),
        },
        {
            "name": "manager_must_delete",
            "description": "manager MUST be permitted to delete any Record",
            "type": "floor",
            "principal_type": "Worker",
            "action": 'Action::"delete"',
            "resource_type": "Record",
            "floor_path": os.path.join(REFS, "manager_must_delete.cedar"),
        },

        # -- Liveness -------------------------------------------------------
        {
            "name": "liveness_view",
            "description": "Worker+view+Record liveness",
            "type": "always-denies-liveness",
            "principal_type": "Worker",
            "action": 'Action::"view"',
            "resource_type": "Record",
        },
        {
            "name": "liveness_edit",
            "description": "Worker+edit+Record liveness",
            "type": "always-denies-liveness",
            "principal_type": "Worker",
            "action": 'Action::"edit"',
            "resource_type": "Record",
        },
        {
            "name": "liveness_delete",
            "description": "Worker+delete+Record liveness",
            "type": "always-denies-liveness",
            "principal_type": "Worker",
            "action": 'Action::"delete"',
            "resource_type": "Record",
        },
    ]
