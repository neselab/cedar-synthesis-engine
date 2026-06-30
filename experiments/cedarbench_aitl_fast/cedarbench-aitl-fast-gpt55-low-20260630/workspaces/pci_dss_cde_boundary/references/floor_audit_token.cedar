// Floor: any System auditing a TOKEN record MUST be permitted.
// Audit of non-PAN data has no extra restrictions.
permit (
    principal is System,
    action == Action::"audit",
    resource is PaymentRecord
)
when {
    resource.dataType == "TOKEN"
};
