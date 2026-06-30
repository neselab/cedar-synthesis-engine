// Floor: an EDD customer with full attestations (uboVerified AND
// adverseMediaClean) MUST be permitted to make a large transfer
// (amount > 100000). This floor respects §8.8 — it asserts only the
// scenario already required by the ceiling.
permit (
    principal is BankCustomer,
    action == Action::"transferOut",
    resource is Transaction
)
when {
    principal.kycTier == "EDD"
    && principal.uboVerified
    && principal.adverseMediaClean
    && resource.amount > 100000
};
