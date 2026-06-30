"""Hand-authored verification plan for realworld/hierarchical_override_three_levels.

Three-level seniority hierarchy (junior=1, senior=2, lead=3) with a
per-level execute override on restrictedAction resources. Tests:
  - 3-level numeric role hierarchy via Long-typed level attribute
  - Per-(level, category) cell encoding (avoids §8.6 role-intersection trap)
  - Asymmetric read/execute permissions: senior CAN read restricted but
    CANNOT execute it (override at the senior level)

Hunts for failure modes:
  - Encoding the override as a forbid keyed on level==2, which composes
    badly with any "senior inherits all" permit
  - Collapsing read and execute into one permit (loses the override)
  - Using `==` comparisons against a single level when the spec implies
    `>=` thresholds (would block leads from reading standard, etc.)
  - Forgetting that senior may READ restrictedAction resources
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceilings ------------------------------------------------
        {
            "name": "read_safety",
            "description": "read permitted only when (level>=1, standard) OR (level>=2, criticalAction) OR (level>=2, restrictedAction)",
            "type": "implies",
            "principal_type": "Employee",
            "action": 'Action::"read"',
            "resource_type": "Resource",
            "reference_path": os.path.join(REFS, "read_safety.cedar"),
        },
        {
            "name": "execute_safety",
            "description": "execute permitted only when (level>=1, standard) OR (level>=2, criticalAction) OR (level>=3, restrictedAction). Senior CANNOT execute restrictedAction.",
            "type": "implies",
            "principal_type": "Employee",
            "action": 'Action::"execute"',
            "resource_type": "Resource",
            "reference_path": os.path.join(REFS, "execute_safety.cedar"),
        },

        # -- Floors ---------------------------------------------------------
        {
            "name": "junior_read_standard",
            "description": "Junior (level 1) MUST be permitted to read standard resources",
            "type": "floor",
            "principal_type": "Employee",
            "action": 'Action::"read"',
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "junior_read_standard.cedar"),
        },
        {
            "name": "junior_execute_standard",
            "description": "Junior (level 1) MUST be permitted to execute standard resources",
            "type": "floor",
            "principal_type": "Employee",
            "action": 'Action::"execute"',
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "junior_execute_standard.cedar"),
        },
        {
            "name": "senior_execute_critical",
            "description": "Senior (level 2) MUST be permitted to execute criticalAction resources",
            "type": "floor",
            "principal_type": "Employee",
            "action": 'Action::"execute"',
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "senior_execute_critical.cedar"),
        },
        {
            "name": "senior_read_restricted",
            "description": "Senior (level 2) MUST be permitted to read restrictedAction resources (the 'view but cannot execute' half of the override)",
            "type": "floor",
            "principal_type": "Employee",
            "action": 'Action::"read"',
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "senior_read_restricted.cedar"),
        },
        {
            "name": "lead_read_restricted",
            "description": "Lead (level 3) MUST be permitted to read restrictedAction resources",
            "type": "floor",
            "principal_type": "Employee",
            "action": 'Action::"read"',
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "lead_read_restricted.cedar"),
        },
        {
            "name": "lead_execute_restricted",
            "description": "Lead (level 3) MUST be permitted to execute restrictedAction resources",
            "type": "floor",
            "principal_type": "Employee",
            "action": 'Action::"execute"',
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "lead_execute_restricted.cedar"),
        },

        # -- Liveness -------------------------------------------------------
        {
            "name": "liveness_read",
            "description": "Employee+read+Resource liveness",
            "type": "always-denies-liveness",
            "principal_type": "Employee",
            "action": 'Action::"read"',
            "resource_type": "Resource",
        },
        {
            "name": "liveness_execute",
            "description": "Employee+execute+Resource liveness",
            "type": "always-denies-liveness",
            "principal_type": "Employee",
            "action": 'Action::"execute"',
            "resource_type": "Resource",
        },
    ]
