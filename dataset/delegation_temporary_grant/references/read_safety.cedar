// Ceiling: read permitted only when (principal is the owner) OR
// (there is an active valid read grant for the principal).
permit (
    principal is User,
    action == Action::"read",
    resource is Resource
)
when {
    principal == resource.owner
    || (
        context has activeGrant
        && context.activeGrant.grantee == principal
        && context.activeGrant.allowedAction == "read"
        && context.activeGrant.expiresAt > context.now.datetime
    )
};
