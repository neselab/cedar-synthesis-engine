// Ceiling: amend permitted only when role == "clinician" AND
//   declaredPurpose == "treatment" AND purposeAttested AND
//   dataCategory == "clinical". Patient authorization does NOT
//   waive amend restrictions (amend flows through §164.526, not §164.508).
permit (
    principal is Workforce,
    action == Action::"amend",
    resource is PatientRecord
)
when {
    principal.role == "clinician"
    && context.purposeAttested
    && context.declaredPurpose == "treatment"
    && resource.dataCategory == "clinical"
};
