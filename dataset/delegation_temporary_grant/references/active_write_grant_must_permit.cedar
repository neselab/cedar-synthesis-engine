// Floor: a non-owner User with a present, active, valid write grant
// MUST be permitted to write the resource.
permit (
    principal is User,
    action == Action::"write",
    resource is Resource
)
when {
    principal != resource.owner
    && context has activeGrant
    && context.activeGrant.grantee == principal
    && context.activeGrant.allowedAction == "write"
    && context.activeGrant.expiresAt > context.now.datetime
};
