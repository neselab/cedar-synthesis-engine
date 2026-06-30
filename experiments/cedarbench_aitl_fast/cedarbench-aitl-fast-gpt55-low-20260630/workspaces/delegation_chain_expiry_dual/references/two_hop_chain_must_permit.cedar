// Floor: a non-owner User at the end of a continuous two-hop
// delegation chain — both grants present, chain-of-trust intact,
// principal is the second delegatee, both windows currently open —
// MUST be permitted to write.
permit (
    principal is User,
    action == Action::"write",
    resource is Resource
)
when {
    principal != resource.owner
    && context has firstGrant
    && context has secondGrant
    && context.firstGrant.delegatee == context.secondGrant.delegator
    && context.secondGrant.delegatee == principal
    && context.firstGrant.grantedAt <= context.now
    && context.firstGrant.expiresAt >= context.now
    && context.secondGrant.grantedAt <= context.now
    && context.secondGrant.expiresAt >= context.now
};
