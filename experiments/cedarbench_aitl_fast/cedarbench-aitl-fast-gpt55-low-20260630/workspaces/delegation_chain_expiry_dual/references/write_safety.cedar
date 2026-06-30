// Ceiling: write permitted only when (principal is the owner) OR
// (single-hop grant active) OR (two-hop chain active during the
// intersection of both windows).
permit (
    principal is User,
    action == Action::"write",
    resource is Resource
)
when {
    principal == resource.owner
    || (
        context has firstGrant
        && context.firstGrant.delegatee == principal
        && context.firstGrant.grantedAt <= context.now
        && context.firstGrant.expiresAt >= context.now
    )
    || (
        context has firstGrant
        && context has secondGrant
        && context.firstGrant.delegatee == context.secondGrant.delegator
        && context.secondGrant.delegatee == principal
        && context.firstGrant.grantedAt <= context.now
        && context.firstGrant.expiresAt >= context.now
        && context.secondGrant.grantedAt <= context.now
        && context.secondGrant.expiresAt >= context.now
    )
};
