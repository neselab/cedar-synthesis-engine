"""Hand-authored verification plan for realworld/implicit_deny_by_default.

Tests the planner's ability to correctly infer Cedar's deny-by-default
convention. The spec lists ONLY the allowed (role, action) combinations
and never explicitly says "anything not listed is denied" — the
synthesizer must rely on Cedar's default-deny semantics.

Hunts for failure modes:
  - Adding spurious `forbid when principal.role == "X"` rules instead
    of relying on positive-permit-only encoding (the §8.6 role-
    intersection trap; even though Worker carries a single role
    string here, a negative-keyed forbid is fragile and brittle).
  - Over-permitting (e.g. nurses permitted to edit, doctors permitted
    to archive) by collapsing role checks.
  - Under-permitting (e.g. forgetting that administrators may also
    view and edit, not only archive).
  - Treating the spec's silence as ambiguity and refusing to emit a
    permit at all.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceilings (one per action) -------------------------------
        {
            "name": "view_safety",
            "description": "view permitted only when principal.role is nurse, doctor, or administrator",
            "type": "implies",
            "principal_type": "Worker",
            "action": 'Action::"view"',
            "resource_type": "Chart",
            "reference_path": os.path.join(REFS, "view_safety.cedar"),
        },
        {
            "name": "edit_safety",
            "description": "edit permitted only when principal.role is doctor or administrator",
            "type": "implies",
            "principal_type": "Worker",
            "action": 'Action::"edit"',
            "resource_type": "Chart",
            "reference_path": os.path.join(REFS, "edit_safety.cedar"),
        },
        {
            "name": "archive_safety",
            "description": "archive permitted only when principal.role is administrator",
            "type": "implies",
            "principal_type": "Worker",
            "action": 'Action::"archive"',
            "resource_type": "Chart",
            "reference_path": os.path.join(REFS, "archive_safety.cedar"),
        },

        # -- Floors ---------------------------------------------------------
        {
            "name": "nurse_view",
            "description": "Nurse MUST be permitted to view any chart",
            "type": "floor",
            "principal_type": "Worker",
            "action": 'Action::"view"',
            "resource_type": "Chart",
            "floor_path": os.path.join(REFS, "nurse_view.cedar"),
        },
        {
            "name": "doctor_view",
            "description": "Doctor MUST be permitted to view any chart",
            "type": "floor",
            "principal_type": "Worker",
            "action": 'Action::"view"',
            "resource_type": "Chart",
            "floor_path": os.path.join(REFS, "doctor_view.cedar"),
        },
        {
            "name": "doctor_edit",
            "description": "Doctor MUST be permitted to edit any chart",
            "type": "floor",
            "principal_type": "Worker",
            "action": 'Action::"edit"',
            "resource_type": "Chart",
            "floor_path": os.path.join(REFS, "doctor_edit.cedar"),
        },
        {
            "name": "admin_edit",
            "description": "Administrator MUST be permitted to edit any chart",
            "type": "floor",
            "principal_type": "Worker",
            "action": 'Action::"edit"',
            "resource_type": "Chart",
            "floor_path": os.path.join(REFS, "admin_edit.cedar"),
        },
        {
            "name": "admin_archive",
            "description": "Administrator MUST be permitted to archive any chart",
            "type": "floor",
            "principal_type": "Worker",
            "action": 'Action::"archive"',
            "resource_type": "Chart",
            "floor_path": os.path.join(REFS, "admin_archive.cedar"),
        },

        # -- Liveness -------------------------------------------------------
        {
            "name": "liveness_view",
            "description": "Worker+view+Chart liveness",
            "type": "always-denies-liveness",
            "principal_type": "Worker",
            "action": 'Action::"view"',
            "resource_type": "Chart",
        },
        {
            "name": "liveness_edit",
            "description": "Worker+edit+Chart liveness",
            "type": "always-denies-liveness",
            "principal_type": "Worker",
            "action": 'Action::"edit"',
            "resource_type": "Chart",
        },
        {
            "name": "liveness_archive",
            "description": "Worker+archive+Chart liveness",
            "type": "always-denies-liveness",
            "principal_type": "Worker",
            "action": 'Action::"archive"',
            "resource_type": "Chart",
        },
    ]
