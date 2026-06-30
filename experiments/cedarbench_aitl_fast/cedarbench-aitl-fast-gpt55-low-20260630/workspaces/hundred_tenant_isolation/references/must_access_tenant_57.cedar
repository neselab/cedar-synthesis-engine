// Floor: a user from tenant_57 MUST be permitted to access a resource from tenant_57.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_57"
    && resource.tenantId == "tenant_57"
};
