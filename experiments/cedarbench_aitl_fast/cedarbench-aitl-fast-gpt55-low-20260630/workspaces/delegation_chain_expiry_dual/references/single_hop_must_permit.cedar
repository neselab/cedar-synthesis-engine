// Floor: a non-owner User holding a single-hop active grant
// (firstGrant present, delegatee == principal, window currently
// open) MUST be permitted to read.
permit (
    principal is User,
    action == Action::"read",
    resource is Resource
)
when {
    principal != resource.owner
    && context has firstGrant
    && context.firstGrant.delegatee == principal
    && context.firstGrant.grantedAt <= context.now
    && context.firstGrant.expiresAt >= context.now
};
