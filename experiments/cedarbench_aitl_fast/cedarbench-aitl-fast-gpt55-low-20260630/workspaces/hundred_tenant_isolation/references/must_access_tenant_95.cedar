// Floor: a user from tenant_95 MUST be permitted to access a resource from tenant_95.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_95"
    && resource.tenantId == "tenant_95"
};
