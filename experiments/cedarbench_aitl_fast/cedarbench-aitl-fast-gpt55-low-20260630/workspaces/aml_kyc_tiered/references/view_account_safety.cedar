// Ceiling: any KYC tier permitted to view own account. Basic identity
// is implied by being onboarded into ANY tier (SDD / CDD / EDD).
permit (
    principal is BankCustomer,
    action == Action::"viewAccount",
    resource is BankCustomer
)
when {
    principal.kycTier == "SDD"
    || principal.kycTier == "CDD"
    || principal.kycTier == "EDD"
};
