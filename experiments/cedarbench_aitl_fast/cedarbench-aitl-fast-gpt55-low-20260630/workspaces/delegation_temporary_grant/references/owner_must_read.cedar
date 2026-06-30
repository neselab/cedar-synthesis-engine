// Floor: the owner MUST be permitted to read their own resource,
// regardless of grant state.
permit (
    principal is User,
    action == Action::"read",
    resource is Resource
)
when {
    principal == resource.owner
};
