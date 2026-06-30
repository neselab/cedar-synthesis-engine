"""Hand-authored verification plan for realworld/deep_entity_hierarchy.

Tests a 5-level entity hierarchy (Employee in Team in Department in
Division in Organization) with classification-based document access.

Exercises Cedar's transitive `in` relation across multiple entity types,
which is the deepest hierarchy chain in the benchmark.

Checks:
  - 3 ceilings (view/edit/delete safety)
  - 5 floors (public view, internal view, confidential view, team edit, team delete)
  - 3 liveness (one per action)
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # ── Safety ceilings ──────────────────────────────────────────────
        {
            "name": "view_safety",
            "description": "view permitted only when public/internal (any employee) or confidential+same-team",
            "type": "implies",
            "principal_type": "Employee",
            "action": 'Action::"view"',
            "resource_type": "Document",
            "reference_path": os.path.join(REFS, "view_safety.cedar"),
        },
        {
            "name": "edit_safety",
            "description": "edit permitted only when same team AND not confidential",
            "type": "implies",
            "principal_type": "Employee",
            "action": 'Action::"edit"',
            "resource_type": "Document",
            "reference_path": os.path.join(REFS, "edit_safety.cedar"),
        },
        {
            "name": "delete_safety",
            "description": "delete permitted only when same team AND public",
            "type": "implies",
            "principal_type": "Employee",
            "action": 'Action::"delete"',
            "resource_type": "Document",
            "reference_path": os.path.join(REFS, "delete_safety.cedar"),
        },

        # ── Floors ───────────────────────────────────────────────────────
        {
            "name": "floor_any_employee_view_public",
            "description": "any employee MUST view public documents",
            "type": "floor",
            "principal_type": "Employee",
            "action": 'Action::"view"',
            "resource_type": "Document",
            "floor_path": os.path.join(REFS, "floor_any_employee_view_public.cedar"),
        },
        {
            "name": "floor_any_employee_view_internal",
            "description": "any employee MUST view internal documents",
            "type": "floor",
            "principal_type": "Employee",
            "action": 'Action::"view"',
            "resource_type": "Document",
            "floor_path": os.path.join(REFS, "floor_any_employee_view_internal.cedar"),
        },
        {
            "name": "floor_team_view_confidential",
            "description": "team member MUST view confidential documents owned by their team",
            "type": "floor",
            "principal_type": "Employee",
            "action": 'Action::"view"',
            "resource_type": "Document",
            "floor_path": os.path.join(REFS, "floor_team_view_confidential.cedar"),
        },
        {
            "name": "floor_team_edit_nonconfidential",
            "description": "team member MUST edit non-confidential documents owned by their team",
            "type": "floor",
            "principal_type": "Employee",
            "action": 'Action::"edit"',
            "resource_type": "Document",
            "floor_path": os.path.join(REFS, "floor_team_edit_nonconfidential.cedar"),
        },
        {
            "name": "floor_team_delete_public",
            "description": "team member MUST delete public documents owned by their team",
            "type": "floor",
            "principal_type": "Employee",
            "action": 'Action::"delete"',
            "resource_type": "Document",
            "floor_path": os.path.join(REFS, "floor_team_delete_public.cedar"),
        },

        # ── Liveness ─────────────────────────────────────────────────────
        {
            "name": "liveness_view",
            "description": "at least one view request must be permitted",
            "type": "always-denies-liveness",
            "principal_type": "Employee",
            "action": 'Action::"view"',
            "resource_type": "Document",
        },
        {
            "name": "liveness_edit",
            "description": "at least one edit request must be permitted",
            "type": "always-denies-liveness",
            "principal_type": "Employee",
            "action": 'Action::"edit"',
            "resource_type": "Document",
        },
        {
            "name": "liveness_delete",
            "description": "at least one delete request must be permitted",
            "type": "always-denies-liveness",
            "principal_type": "Employee",
            "action": 'Action::"delete"',
            "resource_type": "Document",
        },
    ]
