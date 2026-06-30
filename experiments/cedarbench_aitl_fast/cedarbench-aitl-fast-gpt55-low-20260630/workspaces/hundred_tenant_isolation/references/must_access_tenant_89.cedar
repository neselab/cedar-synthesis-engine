// Floor: a user from tenant_89 MUST be permitted to access a resource from tenant_89.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_89"
    && resource.tenantId == "tenant_89"
};
