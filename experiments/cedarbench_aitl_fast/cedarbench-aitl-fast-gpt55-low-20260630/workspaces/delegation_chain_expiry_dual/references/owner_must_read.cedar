// Floor: the resource owner MUST be permitted to read.
permit (
    principal is User,
    action == Action::"read",
    resource is Resource
)
when {
    principal == resource.owner
};
