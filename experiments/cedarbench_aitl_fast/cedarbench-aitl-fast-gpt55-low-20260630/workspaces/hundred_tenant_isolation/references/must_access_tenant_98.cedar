// Floor: a user from tenant_98 MUST be permitted to access a resource from tenant_98.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_98"
    && resource.tenantId == "tenant_98"
};
