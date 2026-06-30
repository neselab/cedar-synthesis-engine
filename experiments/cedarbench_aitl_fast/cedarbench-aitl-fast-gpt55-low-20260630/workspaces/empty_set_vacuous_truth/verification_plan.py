"""Hand-authored verification plan for realworld/empty_set_vacuous_truth.

Tests Cedar's empty-set vacuous-truth semantics:
  [].containsAll(anything) == true
  [].containsAny(anything) == false
  [].contains(anything) == false

The trap: a naive "permit when completedTrainings.containsAll(requiredTrainings)"
permits ANY employee on a workstation whose requiredTrainings is empty,
because vacuous-true. The safe encoding adds an explicit
`!requiredTrainings.isEmpty()` guard. This scenario commits to the safe
default-deny semantics and verifies that the candidate policy honors it.

Checks:
  - 2 ceilings (useWorkstation, bypass)
  - 3 floors (trained employee uses, admin bypass, admin trained also uses)
  - 2 liveness (useWorkstation, bypass)
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # ── Safety ceilings ──────────────────────────────────────────────
        {
            "name": "use_workstation_safety",
            "description": "useWorkstation requires non-empty requirements AND all completed (no vacuous-true permit on empty)",
            "type": "implies",
            "principal_type": "Employee",
            "action": 'Action::"useWorkstation"',
            "resource_type": "Workstation",
            "reference_path": os.path.join(REFS, "use_workstation_safety.cedar"),
        },
        {
            "name": "bypass_safety",
            "description": "bypass permitted only when principal has admin role",
            "type": "implies",
            "principal_type": "Employee",
            "action": 'Action::"bypass"',
            "resource_type": "Workstation",
            "reference_path": os.path.join(REFS, "bypass_safety.cedar"),
        },

        # ── Floors ───────────────────────────────────────────────────────
        {
            "name": "floor_trained_employee_uses",
            "description": "trained employee on configured workstation MUST use it",
            "type": "floor",
            "principal_type": "Employee",
            "action": 'Action::"useWorkstation"',
            "resource_type": "Workstation",
            "floor_path": os.path.join(REFS, "floor_trained_employee_uses.cedar"),
        },
        {
            "name": "floor_admin_bypass",
            "description": "admin MUST be permitted to bypass",
            "type": "floor",
            "principal_type": "Employee",
            "action": 'Action::"bypass"',
            "resource_type": "Workstation",
            "floor_path": os.path.join(REFS, "floor_admin_bypass.cedar"),
        },
        {
            "name": "floor_admin_trained_uses",
            "description": "admin who has all trainings on configured workstation MUST also useWorkstation",
            "type": "floor",
            "principal_type": "Employee",
            "action": 'Action::"useWorkstation"',
            "resource_type": "Workstation",
            "floor_path": os.path.join(REFS, "floor_admin_trained_uses.cedar"),
        },

        # ── Liveness ─────────────────────────────────────────────────────
        {
            "name": "liveness_use_workstation",
            "description": "at least one useWorkstation must be permitted",
            "type": "always-denies-liveness",
            "principal_type": "Employee",
            "action": 'Action::"useWorkstation"',
            "resource_type": "Workstation",
        },
        {
            "name": "liveness_bypass",
            "description": "at least one bypass must be permitted",
            "type": "always-denies-liveness",
            "principal_type": "Employee",
            "action": 'Action::"bypass"',
            "resource_type": "Workstation",
        },
    ]
