// Floor: a non-owner User with a present, active, valid read grant
// MUST be permitted to read the resource.
permit (
    principal is User,
    action == Action::"read",
    resource is Resource
)
when {
    principal != resource.owner
    && context has activeGrant
    && context.activeGrant.grantee == principal
    && context.activeGrant.allowedAction == "read"
    && context.activeGrant.expiresAt > context.now.datetime
};
