// Floor: a request whose context.nonce is present and is in the
// endpoint's validNonces set MUST be permitted to invoke.
//
// has-guard required (§8.3): nonce is optional in the schema, so we
// must guard `context has nonce` before reading `context.nonce`.
permit (
    principal is User,
    action == Action::"invoke",
    resource is CriticalEndpoint
)
when {
    context has nonce && resource.validNonces.contains(context.nonce)
};
