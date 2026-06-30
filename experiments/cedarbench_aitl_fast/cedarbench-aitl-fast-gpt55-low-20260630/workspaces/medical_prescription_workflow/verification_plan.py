"""Hand-authored verification plan for realworld/medical_prescription_workflow.

Controlled-substance prescription workflow with physician/pharmacist/patient/
nurse roles. Tests:
  - Role-based access with ownership guards (prescriber, patient)
  - Boolean state guard (isFilled) preventing double-fill
  - Optional context attribute with has-guard (controlledSubstanceVerified)
  - Conditional context requirement (controlled substances only)

The central safety property: filling a controlled substance requires both
!isFilled AND context.controlledSubstanceVerified == true, with the
optional attribute properly has-guarded.

4 safety ceilings + 9 floors + 4 liveness = 17 total checks.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceilings (one per action) -----------------------------
        {"name": "create_safety", "description": "create permitted only when role == physician", "type": "implies", "principal_type": "User", "action": "Action::\"create\"", "resource_type": "Prescription", "reference_path": os.path.join(REFS, "create_safety.cedar")},
        {"name": "review_safety", "description": "review permitted only when (pharmacist) OR (physician + own prescription) OR (patient + own prescription)", "type": "implies", "principal_type": "User", "action": "Action::\"review\"", "resource_type": "Prescription", "reference_path": os.path.join(REFS, "review_safety.cedar")},
        {"name": "fill_safety", "description": "fill permitted only when (pharmacist AND !isFilled AND (!isControlled OR controlledSubstanceVerified))", "type": "implies", "principal_type": "User", "action": "Action::\"fill\"", "resource_type": "Prescription", "reference_path": os.path.join(REFS, "fill_safety.cedar")},
        {"name": "viewHistory_safety", "description": "viewHistory permitted only when (patient + own) OR (physician + own as prescriber) OR nurse", "type": "implies", "principal_type": "User", "action": "Action::\"viewHistory\"", "resource_type": "Prescription", "reference_path": os.path.join(REFS, "viewHistory_safety.cedar")},

        # -- Floors (positive assertions about what must be permitted) ----
        {"name": "physician_must_create", "description": "Physician MUST be permitted to create prescriptions", "type": "floor", "principal_type": "User", "action": "Action::\"create\"", "resource_type": "Prescription", "floor_path": os.path.join(REFS, "physician_must_create.cedar")},
        {"name": "pharmacist_must_review", "description": "Pharmacist MUST be permitted to review any prescription", "type": "floor", "principal_type": "User", "action": "Action::\"review\"", "resource_type": "Prescription", "floor_path": os.path.join(REFS, "pharmacist_must_review.cedar")},
        {"name": "physician_must_review_own", "description": "Physician MUST be permitted to review prescriptions they wrote", "type": "floor", "principal_type": "User", "action": "Action::\"review\"", "resource_type": "Prescription", "floor_path": os.path.join(REFS, "physician_must_review_own.cedar")},
        {"name": "patient_must_review_own", "description": "Patient MUST be permitted to review their own prescriptions", "type": "floor", "principal_type": "User", "action": "Action::\"review\"", "resource_type": "Prescription", "floor_path": os.path.join(REFS, "patient_must_review_own.cedar")},
        {"name": "pharmacist_must_fill_noncontrolled", "description": "Pharmacist MUST be permitted to fill an unfilled non-controlled prescription", "type": "floor", "principal_type": "User", "action": "Action::\"fill\"", "resource_type": "Prescription", "floor_path": os.path.join(REFS, "pharmacist_must_fill_noncontrolled.cedar")},
        {"name": "pharmacist_must_fill_controlled_verified", "description": "Pharmacist MUST be permitted to fill an unfilled controlled prescription when verification is attested", "type": "floor", "principal_type": "User", "action": "Action::\"fill\"", "resource_type": "Prescription", "floor_path": os.path.join(REFS, "pharmacist_must_fill_controlled_verified.cedar")},
        {"name": "patient_must_viewHistory_own", "description": "Patient MUST be permitted to view history of their own prescriptions", "type": "floor", "principal_type": "User", "action": "Action::\"viewHistory\"", "resource_type": "Prescription", "floor_path": os.path.join(REFS, "patient_must_viewHistory_own.cedar")},
        {"name": "physician_must_viewHistory_own", "description": "Physician MUST be permitted to view history of prescriptions they wrote", "type": "floor", "principal_type": "User", "action": "Action::\"viewHistory\"", "resource_type": "Prescription", "floor_path": os.path.join(REFS, "physician_must_viewHistory_own.cedar")},
        {"name": "nurse_must_viewHistory", "description": "Nurse MUST be permitted to view history of any prescription", "type": "floor", "principal_type": "User", "action": "Action::\"viewHistory\"", "resource_type": "Prescription", "floor_path": os.path.join(REFS, "nurse_must_viewHistory.cedar")},

        # -- Liveness -----------------------------------------------------
        {"name": "liveness_create", "description": "User+create+Prescription liveness", "type": "always-denies-liveness", "principal_type": "User", "action": "Action::\"create\"", "resource_type": "Prescription"},
        {"name": "liveness_review", "description": "User+review+Prescription liveness", "type": "always-denies-liveness", "principal_type": "User", "action": "Action::\"review\"", "resource_type": "Prescription"},
        {"name": "liveness_fill", "description": "User+fill+Prescription liveness", "type": "always-denies-liveness", "principal_type": "User", "action": "Action::\"fill\"", "resource_type": "Prescription"},
        {"name": "liveness_viewHistory", "description": "User+viewHistory+Prescription liveness", "type": "always-denies-liveness", "principal_type": "User", "action": "Action::\"viewHistory\"", "resource_type": "Prescription"},
    ]
