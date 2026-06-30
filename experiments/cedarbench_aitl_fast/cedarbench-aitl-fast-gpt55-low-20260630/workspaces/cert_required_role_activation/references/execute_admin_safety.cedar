// Ceiling: executeAdmin permitted ONLY when EITHER (a) the operator
// has base admin entitlement, OR (b) all four certificate conditions
// hold. Triple has-guard chain on optional cert record (§8.3): every
// read of context.cert.<field> is gated by `context has cert` in the
// same conjunction.
permit (
    principal is Operator,
    action == Action::"executeAdmin",
    resource is Resource
)
when {
    principal.baseRole == "admin"
    || (
        context has cert
        && context.cert.validUntil > context.now
        && context has cert
        && context.cert.claimedRole == "admin"
        && context has cert
        && context.cert.signer == "trusted-ca"
    )
};
