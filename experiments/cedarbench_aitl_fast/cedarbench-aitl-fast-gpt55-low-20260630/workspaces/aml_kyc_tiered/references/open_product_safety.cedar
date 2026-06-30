// Ceiling: openProduct permitted only when:
//   - High-risk principal (riskScore > 70): EDD AND uboVerified
//     AND adverseMediaClean.
//   - Standard (riskScore <= 70): CDD or EDD (SDD never permitted).
permit (
    principal is BankCustomer,
    action == Action::"openProduct",
    resource is BankCustomer
)
when {
    (principal.riskScore > 70
        && principal.kycTier == "EDD"
        && principal.uboVerified
        && principal.adverseMediaClean)
    || (principal.riskScore <= 70
        && (principal.kycTier == "CDD" || principal.kycTier == "EDD"))
};
