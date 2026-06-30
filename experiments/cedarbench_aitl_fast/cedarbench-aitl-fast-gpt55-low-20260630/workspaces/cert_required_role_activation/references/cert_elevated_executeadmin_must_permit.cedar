// Floor: a non-admin operator who presents a valid, unexpired
// admin-claiming cert signed by "trusted-ca" MUST be permitted to
// executeAdmin. Mirrors branch (b) of the ceiling. Triple has-guard
// chain on the optional cert record.
permit (
    principal is Operator,
    action == Action::"executeAdmin",
    resource is Resource
)
when {
    context has cert
    && context.cert.validUntil > context.now
    && context has cert
    && context.cert.claimedRole == "admin"
    && context has cert
    && context.cert.signer == "trusted-ca"
};
