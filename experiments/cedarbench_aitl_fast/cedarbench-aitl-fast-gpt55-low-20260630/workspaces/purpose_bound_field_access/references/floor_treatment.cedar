// Floor: a clinician declaring "treatment" requesting a field that is in
// the record's treatment-allowlist MUST be permitted. The candidate must
// be at least this permissive on the treatment branch.
permit (
    principal is Workforce,
    action == Action::"accessField",
    resource is PatientRecord
)
when {
    principal.role == "clinician"
    && context.declaredPurpose == "treatment"
    && resource.purposeFieldsTreatment.contains(context.requestedField)
};
