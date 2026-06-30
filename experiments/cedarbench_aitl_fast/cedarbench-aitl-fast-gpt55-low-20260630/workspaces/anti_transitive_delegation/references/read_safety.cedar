// Ceiling: read permitted only when (principal is the owner) OR
// (there is a depth-1 delegation grant naming this principal as
// delegatee, originating from the owner, for this resource).
permit (
    principal is User,
    action == Action::"read",
    resource is Resource
)
when {
    principal == resource.owner
    || (
        context has delegationGrant
        && context.delegationGrant.delegatee == principal
        && context.delegationGrant.delegator == resource.owner
        && context.delegationGrant.resource == resource
        && context.delegationGrant.depth == 1
    )
};
