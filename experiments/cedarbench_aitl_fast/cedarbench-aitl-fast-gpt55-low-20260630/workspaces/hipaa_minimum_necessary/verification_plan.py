"""Hand-authored verification plan for realworld/hipaa_minimum_necessary.

HIPAA §164.502(b) Minimum Necessary Rule with purpose-bound field access.
Tests:
  - Role-purpose-category 3-way conjunction matrix (4 role branches)
  - Optional context attribute with has-guard (patientAuthorized)
  - Action-specific context requirement (disclosureLog only for disclose)
  - Authorization override (patient consent waives minimum necessary for
    view/disclose, but NOT for amend)
  - Attestation gate applying across all actions

Central safety property: the role-purpose-category matrix is the ceiling;
patient authorization provides the sole override for view/disclose;
amend is the tightest ceiling with no override.

3 ceilings + 7 floors + 3 liveness = 13 total checks.
"""
import os

REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "references")


def get_checks():
    return [
        # -- Safety ceilings (one per action) -----------------------------
        {"name": "view_safety", "description": "view permitted only when purposeAttested AND (role-purpose-category matrix OR patient-authorized override)", "type": "implies", "principal_type": "Workforce", "action": "Action::\"view\"", "resource_type": "PatientRecord", "reference_path": os.path.join(REFS, "view_safety.cedar")},
        {"name": "disclose_safety", "description": "disclose permitted only when purposeAttested AND disclosureLog AND (role-purpose-category matrix OR patient-authorized override)", "type": "implies", "principal_type": "Workforce", "action": "Action::\"disclose\"", "resource_type": "PatientRecord", "reference_path": os.path.join(REFS, "disclose_safety.cedar")},
        {"name": "amend_safety", "description": "amend permitted only when clinician + treatment + attested + clinical category (no patient-auth override for amend)", "type": "implies", "principal_type": "Workforce", "action": "Action::\"amend\"", "resource_type": "PatientRecord", "reference_path": os.path.join(REFS, "amend_safety.cedar")},

        # -- Floors (positive assertions about what must be permitted) ----
        {"name": "clinician_must_view_clinical", "description": "Clinician with attested treatment purpose MUST be permitted to view clinical records", "type": "floor", "principal_type": "Workforce", "action": "Action::\"view\"", "resource_type": "PatientRecord", "floor_path": os.path.join(REFS, "clinician_must_view_clinical.cedar")},
        {"name": "billing_must_view_billing", "description": "Billing with attested payment purpose MUST be permitted to view billing records", "type": "floor", "principal_type": "Workforce", "action": "Action::\"view\"", "resource_type": "PatientRecord", "floor_path": os.path.join(REFS, "billing_must_view_billing.cedar")},
        {"name": "researcher_must_view_research", "description": "Researcher with attested research purpose MUST be permitted to view research records", "type": "floor", "principal_type": "Workforce", "action": "Action::\"view\"", "resource_type": "PatientRecord", "floor_path": os.path.join(REFS, "researcher_must_view_research.cedar")},
        {"name": "privacy_officer_must_view_any", "description": "Privacy officer with attested operations purpose MUST be permitted to view any record (oversight)", "type": "floor", "principal_type": "Workforce", "action": "Action::\"view\"", "resource_type": "PatientRecord", "floor_path": os.path.join(REFS, "privacy_officer_must_view_any.cedar")},
        {"name": "patient_authorized_override_view", "description": "When patientAuthorized is present and true, any attested workforce member MUST be permitted to view (§164.508 override)", "type": "floor", "principal_type": "Workforce", "action": "Action::\"view\"", "resource_type": "PatientRecord", "floor_path": os.path.join(REFS, "patient_authorized_override_view.cedar")},
        {"name": "clinician_must_disclose_clinical", "description": "Clinician with attested treatment purpose AND disclosureLog MUST be permitted to disclose clinical records", "type": "floor", "principal_type": "Workforce", "action": "Action::\"disclose\"", "resource_type": "PatientRecord", "floor_path": os.path.join(REFS, "clinician_must_disclose_clinical.cedar")},
        {"name": "clinician_must_amend_clinical", "description": "Clinician with attested treatment purpose MUST be permitted to amend clinical records", "type": "floor", "principal_type": "Workforce", "action": "Action::\"amend\"", "resource_type": "PatientRecord", "floor_path": os.path.join(REFS, "clinician_must_amend_clinical.cedar")},

        # -- Liveness -----------------------------------------------------
        {"name": "liveness_view", "description": "Workforce+view+PatientRecord liveness", "type": "always-denies-liveness", "principal_type": "Workforce", "action": "Action::\"view\"", "resource_type": "PatientRecord"},
        {"name": "liveness_disclose", "description": "Workforce+disclose+PatientRecord liveness", "type": "always-denies-liveness", "principal_type": "Workforce", "action": "Action::\"disclose\"", "resource_type": "PatientRecord"},
        {"name": "liveness_amend", "description": "Workforce+amend+PatientRecord liveness", "type": "always-denies-liveness", "principal_type": "Workforce", "action": "Action::\"amend\"", "resource_type": "PatientRecord"},
    ]
