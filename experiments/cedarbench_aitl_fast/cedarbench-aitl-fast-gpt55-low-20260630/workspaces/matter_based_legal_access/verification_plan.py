"""Hand-authored verification plan for realworld/matter_based_legal_access.

Law firm matter-based access control where attorneys, paralegals, and
staff can only act on documents belonging to their assigned matters.
Attorney-client privileged documents have additional role restrictions
(partner-only). Tests:
  - Set.contains() for matter-assignment gate
  - Role-based action restrictions (edit, file, redact)
  - Privileged-document overlay (partner-only across all actions)
  - Composition of set membership with role checks
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceilings ------------------------------------------------
        {"name": "view_safety", "description": "view permitted only when assigned to matter AND (not privileged OR role is partner)", "type": "implies", "principal_type": "User", "action": "Action::\"view\"", "resource_type": "Document", "reference_path": os.path.join(REFS, "view_safety.cedar")},
        {"name": "edit_safety", "description": "edit permitted only when assigned to matter AND role is associate or partner AND (not privileged OR role is partner)", "type": "implies", "principal_type": "User", "action": "Action::\"edit\"", "resource_type": "Document", "reference_path": os.path.join(REFS, "edit_safety.cedar")},
        {"name": "file_safety", "description": "file permitted only when assigned to matter AND (not privileged OR role is partner)", "type": "implies", "principal_type": "User", "action": "Action::\"file\"", "resource_type": "Document", "reference_path": os.path.join(REFS, "file_safety.cedar")},
        {"name": "redact_safety", "description": "redact permitted only when assigned to matter AND role is partner", "type": "implies", "principal_type": "User", "action": "Action::\"redact\"", "resource_type": "Document", "reference_path": os.path.join(REFS, "redact_safety.cedar")},

        # -- Floors ---------------------------------------------------------
        {"name": "associate_must_view", "description": "Associate assigned to matter MUST view non-privileged document", "type": "floor", "principal_type": "User", "action": "Action::\"view\"", "resource_type": "Document", "floor_path": os.path.join(REFS, "associate_must_view.cedar")},
        {"name": "partner_must_view_privileged", "description": "Partner assigned to matter MUST view privileged document", "type": "floor", "principal_type": "User", "action": "Action::\"view\"", "resource_type": "Document", "floor_path": os.path.join(REFS, "partner_must_view_privileged.cedar")},
        {"name": "associate_must_edit", "description": "Associate assigned to matter MUST edit non-privileged document", "type": "floor", "principal_type": "User", "action": "Action::\"edit\"", "resource_type": "Document", "floor_path": os.path.join(REFS, "associate_must_edit.cedar")},
        {"name": "paralegal_must_file", "description": "Paralegal assigned to matter MUST file non-privileged document", "type": "floor", "principal_type": "User", "action": "Action::\"file\"", "resource_type": "Document", "floor_path": os.path.join(REFS, "paralegal_must_file.cedar")},
        {"name": "partner_must_redact", "description": "Partner assigned to matter MUST redact non-privileged document", "type": "floor", "principal_type": "User", "action": "Action::\"redact\"", "resource_type": "Document", "floor_path": os.path.join(REFS, "partner_must_redact.cedar")},

        # -- Liveness -------------------------------------------------------
        {"name": "liveness_view", "description": "User+view+Document liveness", "type": "always-denies-liveness", "principal_type": "User", "action": "Action::\"view\"", "resource_type": "Document"},
        {"name": "liveness_edit", "description": "User+edit+Document liveness", "type": "always-denies-liveness", "principal_type": "User", "action": "Action::\"edit\"", "resource_type": "Document"},
    ]
