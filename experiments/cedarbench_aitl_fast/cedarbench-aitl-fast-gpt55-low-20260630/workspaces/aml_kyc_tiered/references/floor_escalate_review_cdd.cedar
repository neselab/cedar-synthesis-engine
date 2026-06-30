// Floor: a CDD customer MUST be permitted to file a compliance
// escalation. This is the lowest tier eligible for escalateReview.
permit (
    principal is BankCustomer,
    action == Action::"escalateReview",
    resource is BankCustomer
)
when {
    principal.kycTier == "CDD"
};
