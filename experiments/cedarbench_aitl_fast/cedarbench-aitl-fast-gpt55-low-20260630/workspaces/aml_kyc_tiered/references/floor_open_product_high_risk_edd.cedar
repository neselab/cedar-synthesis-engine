// Floor: a high-risk EDD customer with full attestations (uboVerified
// AND adverseMediaClean) MUST be permitted to open a product. This is
// the EDD path — the only path available to high-risk principals.
permit (
    principal is BankCustomer,
    action == Action::"openProduct",
    resource is BankCustomer
)
when {
    principal.riskScore > 70
    && principal.kycTier == "EDD"
    && principal.uboVerified
    && principal.adverseMediaClean
};
