// Floor: a user MUST be permitted to readResource when the resource is
// in the same tenant as the user.
permit (
    principal is User,
    action == Action::"readResource",
    resource is Resource
)
when {
    principal.tenant == resource.tenant
};
