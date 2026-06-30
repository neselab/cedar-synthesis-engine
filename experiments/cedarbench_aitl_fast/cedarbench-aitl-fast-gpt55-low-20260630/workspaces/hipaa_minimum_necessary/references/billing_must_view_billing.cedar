// Floor: a billing workforce member with attested payment purpose MUST
// be permitted to view a billing-category PatientRecord.
permit (
    principal is Workforce,
    action == Action::"view",
    resource is PatientRecord
)
when {
    principal.role == "billing"
    && context.purposeAttested
    && context.declaredPurpose == "payment"
    && resource.dataCategory == "billing"
};
