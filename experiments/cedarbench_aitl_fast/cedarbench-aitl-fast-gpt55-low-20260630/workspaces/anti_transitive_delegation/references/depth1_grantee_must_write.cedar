// Floor: a non-owner User holding a depth-1 grant from the resource
// owner, naming this resource and themselves as delegatee, MUST be
// permitted to write.
permit (
    principal is User,
    action == Action::"write",
    resource is Resource
)
when {
    principal != resource.owner
    && context has delegationGrant
    && context.delegationGrant.delegatee == principal
    && context.delegationGrant.delegator == resource.owner
    && context.delegationGrant.resource == resource
    && context.delegationGrant.depth == 1
};
