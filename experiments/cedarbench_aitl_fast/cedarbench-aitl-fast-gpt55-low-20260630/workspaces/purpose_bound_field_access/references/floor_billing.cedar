// Floor: a billing clerk declaring "billing" requesting a field in the
// record's billing-allowlist MUST be permitted.
permit (
    principal is Workforce,
    action == Action::"accessField",
    resource is PatientRecord
)
when {
    principal.role == "billing_clerk"
    && context.declaredPurpose == "billing"
    && resource.purposeFieldsBilling.contains(context.requestedField)
};
