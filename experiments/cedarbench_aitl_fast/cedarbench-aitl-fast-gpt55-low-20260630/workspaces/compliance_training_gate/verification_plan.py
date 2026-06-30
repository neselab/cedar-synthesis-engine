"""Hand-authored verification plan for realworld/compliance_training_gate.

Access gated on completion of required compliance training. Tests:
  - containsAll set operation (employee trainings >= system requirements)
  - Boolean sensitivity flag blocking export on sensitive systems
  - Role-based action restriction (manager-only adminConfig)
  - Compositional permit conditions (training + sensitivity, training + role)

Checks:
  - 3 ceilings (access/export/adminConfig safety)
  - 3 floors (trained access, trained export non-sensitive, manager admin)
  - 3 liveness
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceilings ------------------------------------------------
        {
            "name": "access_safety",
            "description": "access permitted only when employee has completed all required trainings",
            "type": "implies",
            "principal_type": "Employee",
            "action": 'Action::"access"',
            "resource_type": "System",
            "reference_path": os.path.join(REFS, "access_safety.cedar"),
        },
        {
            "name": "export_safety",
            "description": "export permitted only when training gate met AND system is not sensitive",
            "type": "implies",
            "principal_type": "Employee",
            "action": 'Action::"export"',
            "resource_type": "System",
            "reference_path": os.path.join(REFS, "export_safety.cedar"),
        },
        {
            "name": "admin_config_safety",
            "description": "adminConfig permitted only when employee is a manager AND training gate met",
            "type": "implies",
            "principal_type": "Employee",
            "action": 'Action::"adminConfig"',
            "resource_type": "System",
            "reference_path": os.path.join(REFS, "admin_config_safety.cedar"),
        },

        # -- Floors ---------------------------------------------------------
        {
            "name": "floor_trained_access",
            "description": "employee who completed all required trainings MUST be able to access",
            "type": "floor",
            "principal_type": "Employee",
            "action": 'Action::"access"',
            "resource_type": "System",
            "floor_path": os.path.join(REFS, "floor_trained_access.cedar"),
        },
        {
            "name": "floor_trained_export_nonsensitive",
            "description": "trained employee MUST be able to export from non-sensitive system",
            "type": "floor",
            "principal_type": "Employee",
            "action": 'Action::"export"',
            "resource_type": "System",
            "floor_path": os.path.join(REFS, "floor_trained_export_nonsensitive.cedar"),
        },
        {
            "name": "floor_manager_admin",
            "description": "trained manager MUST be able to adminConfig",
            "type": "floor",
            "principal_type": "Employee",
            "action": 'Action::"adminConfig"',
            "resource_type": "System",
            "floor_path": os.path.join(REFS, "floor_manager_admin.cedar"),
        },

        # -- Liveness -------------------------------------------------------
        {
            "name": "liveness_access",
            "description": "Employee+access+System liveness",
            "type": "always-denies-liveness",
            "principal_type": "Employee",
            "action": 'Action::"access"',
            "resource_type": "System",
        },
        {
            "name": "liveness_export",
            "description": "Employee+export+System liveness",
            "type": "always-denies-liveness",
            "principal_type": "Employee",
            "action": 'Action::"export"',
            "resource_type": "System",
        },
        {
            "name": "liveness_admin_config",
            "description": "Employee+adminConfig+System liveness",
            "type": "always-denies-liveness",
            "principal_type": "Employee",
            "action": 'Action::"adminConfig"',
            "resource_type": "System",
        },
    ]
