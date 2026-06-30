permit (
    principal is User,
    action in [Action::"read", Action::"write"],
    resource is Resource
) when {
    principal == resource.owner
};

permit (
    principal is User,
    action in [Action::"read", Action::"write"],
    resource is Resource
) when {
    context has delegationGrant &&
    context.delegationGrant.delegatee == principal &&
    context.delegationGrant.delegator == resource.owner &&
    context.delegationGrant.resource == resource &&
    context.delegationGrant.depth == 1
};

permit (
    principal is User,
    action == Action::"delegate",
    resource is Resource
) when {
    principal == resource.owner
};