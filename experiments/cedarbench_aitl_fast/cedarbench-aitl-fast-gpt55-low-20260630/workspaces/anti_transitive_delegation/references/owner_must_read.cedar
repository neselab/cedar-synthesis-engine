// Floor: the resource owner MUST be permitted to read their own
// resource. (No grant lookup required.)
permit (
    principal is User,
    action == Action::"read",
    resource is Resource
)
when {
    principal == resource.owner
};
