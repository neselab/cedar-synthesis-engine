// Floor: the owner MUST be permitted to write their own resource.
permit (
    principal is User,
    action == Action::"write",
    resource is Resource
)
when {
    principal == resource.owner
};
