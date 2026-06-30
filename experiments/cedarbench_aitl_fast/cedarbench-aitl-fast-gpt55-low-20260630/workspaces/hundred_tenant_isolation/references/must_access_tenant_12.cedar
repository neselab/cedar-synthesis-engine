// Floor: a user from tenant_12 MUST be permitted to access a resource from tenant_12.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_12"
    && resource.tenantId == "tenant_12"
};
