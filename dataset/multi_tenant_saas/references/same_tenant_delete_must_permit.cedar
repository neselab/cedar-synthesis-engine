// Floor: a user MUST be permitted to deleteResource on a resource in
// the same tenant.
permit (
    principal is User,
    action == Action::"deleteResource",
    resource is Resource
)
when {
    principal.tenant == resource.tenant
};
