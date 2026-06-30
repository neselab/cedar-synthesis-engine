// Floor: a clinician with attested treatment purpose MUST be permitted
// to view a clinical PatientRecord.
permit (
    principal is Workforce,
    action == Action::"view",
    resource is PatientRecord
)
when {
    principal.role == "clinician"
    && context.purposeAttested
    && context.declaredPurpose == "treatment"
    && resource.dataCategory == "clinical"
};
