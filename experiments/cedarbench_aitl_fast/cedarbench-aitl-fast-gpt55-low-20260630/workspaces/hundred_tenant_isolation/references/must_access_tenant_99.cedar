// Floor: a user from tenant_99 MUST be permitted to access a resource from tenant_99.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_99"
    && resource.tenantId == "tenant_99"
};
