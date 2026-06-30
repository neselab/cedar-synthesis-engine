// Floor: ANY User (no role/identity gating) with a valid nonce MUST
// be permitted to invoke. This pins down that the policy must NOT add
// a per-principal restriction beyond the nonce check -- nonce
// possession alone is sufficient authorization.
//
// has-guard required (§8.3) before reading context.nonce.
permit (
    principal is User,
    action == Action::"invoke",
    resource is CriticalEndpoint
)
when {
    context has nonce && resource.validNonces.contains(context.nonce)
};
