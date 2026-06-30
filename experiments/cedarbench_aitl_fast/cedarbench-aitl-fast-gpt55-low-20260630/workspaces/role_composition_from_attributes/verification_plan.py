"""Hand-authored verification plan for realworld/role_composition_from_attributes.

Effective-role computed inline from an attribute conjunction. There is
NO `principal.role` attribute on `Employee` — the schema declares only
`seniority: Long`, `certifications: Set<String>`, and
`employmentStatus: String`. The "manager" role is computed inline as
the conjunction of three predicates.

Hunts for the failure modes where the synthesizer:
  (a) imagines a `principal.role` attribute and writes
      `principal.role == "manager"` (schema-validation failure),
  (b) drops one of the three manager conjuncts (breaks
      `manage_safety` ceiling),
  (c) gates `view` on the manager predicate (breaks
      `junior_active_view_must_permit` floor),
  (d) forgets the `employmentStatus == "active"` gate on `view`
      (breaks `view_safety` ceiling),
  (e) uses `containsAll` / `containsAny` incorrectly instead of
      `contains` for the single-string MGMT-101 check.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceilings --------------------------------------------------
        {
            "name": "view_safety",
            "description": (
                "view permitted only when principal.employmentStatus == 'active'"
            ),
            "type": "implies",
            "principal_type": "Employee",
            "action": 'Action::"view"',
            "resource_type": "Resource",
            "reference_path": os.path.join(REFS, "view_safety.cedar"),
        },
        {
            "name": "manage_safety",
            "description": (
                "manage permitted only when ALL three effective-manager "
                "predicates hold: employmentStatus == 'active' AND "
                "seniority >= 5 AND certifications.contains('MGMT-101')"
            ),
            "type": "implies",
            "principal_type": "Employee",
            "action": 'Action::"manage"',
            "resource_type": "Resource",
            "reference_path": os.path.join(REFS, "manage_safety.cedar"),
        },

        # -- Floors -----------------------------------------------------------
        {
            "name": "active_employee_view_must_permit",
            "description": (
                "any employee with employmentStatus == 'active' MUST be "
                "able to view"
            ),
            "type": "floor",
            "principal_type": "Employee",
            "action": 'Action::"view"',
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "active_employee_view_must_permit.cedar"),
        },
        {
            "name": "junior_active_view_must_permit",
            "description": (
                "a junior active employee (seniority < 5, no MGMT-101) "
                "MUST still be permitted to view — view is NOT gated on "
                "the manager predicate"
            ),
            "type": "floor",
            "principal_type": "Employee",
            "action": 'Action::"view"',
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "junior_active_view_must_permit.cedar"),
        },
        {
            "name": "effective_manager_manage_must_permit",
            "description": (
                "an active employee with seniority >= 5 AND the MGMT-101 "
                "certification MUST be permitted to manage"
            ),
            "type": "floor",
            "principal_type": "Employee",
            "action": 'Action::"manage"',
            "resource_type": "Resource",
            "floor_path": os.path.join(REFS, "effective_manager_manage_must_permit.cedar"),
        },

        # -- Liveness ---------------------------------------------------------
        {
            "name": "liveness_view",
            "description": "Employee+view+Resource liveness",
            "type": "always-denies-liveness",
            "principal_type": "Employee",
            "action": 'Action::"view"',
            "resource_type": "Resource",
        },
        {
            "name": "liveness_manage",
            "description": "Employee+manage+Resource liveness",
            "type": "always-denies-liveness",
            "principal_type": "Employee",
            "action": 'Action::"manage"',
            "resource_type": "Resource",
        },
    ]
