// Floor: a user from tenant_0 MUST be permitted to access a resource from tenant_0.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_0"
    && resource.tenantId == "tenant_0"
};
