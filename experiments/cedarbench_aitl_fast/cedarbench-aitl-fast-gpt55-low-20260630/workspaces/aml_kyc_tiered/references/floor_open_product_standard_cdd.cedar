// Floor: a standard-risk (riskScore <= 70) CDD customer MUST be
// permitted to open a product.
permit (
    principal is BankCustomer,
    action == Action::"openProduct",
    resource is BankCustomer
)
when {
    principal.riskScore <= 70
    && principal.kycTier == "CDD"
};
