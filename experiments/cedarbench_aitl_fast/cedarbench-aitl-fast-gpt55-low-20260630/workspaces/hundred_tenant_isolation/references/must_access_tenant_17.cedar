// Floor: a user from tenant_17 MUST be permitted to access a resource from tenant_17.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_17"
    && resource.tenantId == "tenant_17"
};
