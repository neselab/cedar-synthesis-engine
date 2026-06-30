// Ceiling: write permitted only when (principal is the owner) OR
// (there is an active valid write grant for the principal).
permit (
    principal is User,
    action == Action::"write",
    resource is Resource
)
when {
    principal == resource.owner
    || (
        context has activeGrant
        && context.activeGrant.grantee == principal
        && context.activeGrant.allowedAction == "write"
        && context.activeGrant.expiresAt > context.now.datetime
    )
};
