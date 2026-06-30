// Floor: any System reading a TOKEN record MUST be permitted.
// Tokens are not sensitive — that is the point of tokenization.
permit (
    principal is System,
    action == Action::"read",
    resource is PaymentRecord
)
when {
    resource.dataType == "TOKEN"
};
