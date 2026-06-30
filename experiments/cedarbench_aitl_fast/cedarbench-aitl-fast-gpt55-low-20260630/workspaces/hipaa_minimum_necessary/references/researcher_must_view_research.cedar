// Floor: a researcher with attested research purpose MUST be permitted
// to view a research-category PatientRecord.
permit (
    principal is Workforce,
    action == Action::"view",
    resource is PatientRecord
)
when {
    principal.role == "researcher"
    && context.purposeAttested
    && context.declaredPurpose == "research"
    && resource.dataCategory == "research"
};
