// Floor: a user MUST be permitted to writeResource on a resource in the
// same tenant.
permit (
    principal is User,
    action == Action::"writeResource",
    resource is Resource
)
when {
    principal.tenant == resource.tenant
};
