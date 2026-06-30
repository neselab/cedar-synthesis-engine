// Ceiling: transferOut permitted only when verification depth matches
// the amount band.
//   amount < 10000          -> any tier (SDD / CDD / EDD)
//   10000 <= amount <= 100000 -> CDD or EDD
//   amount > 100000         -> EDD AND uboVerified AND adverseMediaClean
//
// Encoded as positive permits per amount band — NOT as forbids on
// SDD (per §8.6 role-intersection trap).
permit (
    principal is BankCustomer,
    action == Action::"transferOut",
    resource is Transaction
)
when {
    (resource.amount < 10000
        && (principal.kycTier == "SDD"
            || principal.kycTier == "CDD"
            || principal.kycTier == "EDD"))
    || (resource.amount >= 10000 && resource.amount <= 100000
        && (principal.kycTier == "CDD" || principal.kycTier == "EDD"))
    || (resource.amount > 100000
        && principal.kycTier == "EDD"
        && principal.uboVerified
        && principal.adverseMediaClean)
};
