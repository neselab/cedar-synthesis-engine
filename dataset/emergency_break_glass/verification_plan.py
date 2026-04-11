"""Hand-authored verification plan for realworld/emergency_break_glass.

Real-world healthcare break-glass pattern. Tests:
  - Same-hospital baseline (no cross-hospital access under any condition)
  - Care-team standard access (view + edit)
  - Narrow break-glass view-only override (on-call + emergency + reason)
  - Separation of view and edit paths under emergency conditions

The key safety property being verified is that break-glass unlocks only
viewing, never editing, even for on-call clinicians during an active
emergency. An over-permissive candidate that extends break-glass to
edits will fail `edit_safety`.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # ── Safety ceilings ──────────────────────────────────────────────
        {
            "name": "view_safety",
            "description": "viewRecord permitted only when same-hospital AND (care-team OR break-glass conditions)",
            "type": "implies",
            "principal_type": "Clinician",
            "action": "Action::\"viewRecord\"",
            "resource_type": "Record",
            "reference_path": os.path.join(REFS, "view_safety.cedar"),
        },
        {
            "name": "edit_safety",
            "description": "editRecord permitted only when same-hospital AND care-team (break-glass does NOT authorize edits)",
            "type": "implies",
            "principal_type": "Clinician",
            "action": "Action::\"editRecord\"",
            "resource_type": "Record",
            "reference_path": os.path.join(REFS, "edit_safety.cedar"),
        },

        # ── Positive floors ──────────────────────────────────────────────
        {
            "name": "careteam_view_must_permit",
            "description": "Same-hospital care-team member MUST be permitted to viewRecord",
            "type": "floor",
            "principal_type": "Clinician",
            "action": "Action::\"viewRecord\"",
            "resource_type": "Record",
            "floor_path": os.path.join(REFS, "careteam_view_must_permit.cedar"),
        },
        {
            "name": "careteam_edit_must_permit",
            "description": "Same-hospital care-team member MUST be permitted to editRecord",
            "type": "floor",
            "principal_type": "Clinician",
            "action": "Action::\"editRecord\"",
            "resource_type": "Record",
            "floor_path": os.path.join(REFS, "careteam_edit_must_permit.cedar"),
        },
        {
            "name": "break_glass_view_must_permit",
            "description": "On-call clinician at same hospital with active emergency and non-empty reason MUST be permitted to viewRecord for a non-care-team patient",
            "type": "floor",
            "principal_type": "Clinician",
            "action": "Action::\"viewRecord\"",
            "resource_type": "Record",
            "floor_path": os.path.join(REFS, "break_glass_view_must_permit.cedar"),
        },

        # ── Liveness ─────────────────────────────────────────────────────
        {
            "name": "liveness_view_record",
            "description": "Clinician+viewRecord+Record has at least one permitted request",
            "type": "always-denies-liveness",
            "principal_type": "Clinician",
            "action": "Action::\"viewRecord\"",
            "resource_type": "Record",
        },
        {
            "name": "liveness_edit_record",
            "description": "Clinician+editRecord+Record has at least one permitted request",
            "type": "always-denies-liveness",
            "principal_type": "Clinician",
            "action": "Action::\"editRecord\"",
            "resource_type": "Record",
        },
    ]
