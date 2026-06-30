// Floor: an SDD customer MUST be permitted to make a small transfer
// (amount < 10000). This is the lowest tier-amount band.
permit (
    principal is BankCustomer,
    action == Action::"transferOut",
    resource is Transaction
)
when {
    principal.kycTier == "SDD"
    && resource.amount < 10000
};
