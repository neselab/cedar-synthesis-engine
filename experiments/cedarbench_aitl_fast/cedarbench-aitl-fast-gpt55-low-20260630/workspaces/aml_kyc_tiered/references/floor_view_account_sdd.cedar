// Floor: an SDD customer MUST be able to view their own account.
// Smallest viable case for viewAccount.
permit (
    principal is BankCustomer,
    action == Action::"viewAccount",
    resource is BankCustomer
)
when {
    principal.kycTier == "SDD"
};
