// Floor: a researcher declaring "research" requesting a field in the
// record's research-allowlist MUST be permitted.
permit (
    principal is Workforce,
    action == Action::"accessField",
    resource is PatientRecord
)
when {
    principal.role == "researcher"
    && context.declaredPurpose == "research"
    && resource.purposeFieldsResearch.contains(context.requestedField)
};
