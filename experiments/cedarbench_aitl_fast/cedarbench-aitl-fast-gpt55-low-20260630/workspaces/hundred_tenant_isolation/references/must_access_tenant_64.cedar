// Floor: a user from tenant_64 MUST be permitted to access a resource from tenant_64.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_64"
    && resource.tenantId == "tenant_64"
};
