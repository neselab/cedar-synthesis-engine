// Floor: a CDD customer MUST be permitted to make a mid-band transfer
// (10000 <= amount <= 100000).
permit (
    principal is BankCustomer,
    action == Action::"transferOut",
    resource is Transaction
)
when {
    principal.kycTier == "CDD"
    && resource.amount >= 10000
    && resource.amount <= 100000
};
