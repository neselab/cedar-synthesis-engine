// Ceiling: read permitted only when (principal is the owner) OR
// (single-hop grant: firstGrant present, delegatee == principal,
// window currently open) OR (two-hop chain: both grants present,
// chain-of-trust continuous, principal is the second delegatee,
// both windows currently open).
permit (
    principal is User,
    action == Action::"read",
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
