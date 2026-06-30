// Ceiling: escalateReview permitted only for compliance-aware tiers
// (CDD or EDD). SDD customers cannot file escalations.
permit (
    principal is BankCustomer,
    action == Action::"escalateReview",
    resource is BankCustomer
)
when {
    principal.kycTier == "CDD" || principal.kycTier == "EDD"
};
