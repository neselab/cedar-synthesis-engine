// Floor: a clinician with attested treatment purpose MUST be permitted
// to amend a clinical PatientRecord.
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
