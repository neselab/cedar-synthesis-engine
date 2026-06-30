// Floor: a user from tenant_67 MUST be permitted to access a resource from tenant_67.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_67"
    && resource.tenantId == "tenant_67"
};
