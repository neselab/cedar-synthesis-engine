// Floor: any System reading a MASKED_PAN record MUST be permitted.
// Masked data is safe to expose broadly.
permit (
    principal is System,
    action == Action::"read",
    resource is PaymentRecord
)
when {
    resource.dataType == "MASKED_PAN"
};
