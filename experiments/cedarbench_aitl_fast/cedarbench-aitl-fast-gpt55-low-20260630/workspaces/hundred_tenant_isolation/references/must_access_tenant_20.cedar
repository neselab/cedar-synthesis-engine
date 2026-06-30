// Floor: a user from tenant_20 MUST be permitted to access a resource from tenant_20.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_20"
    && resource.tenantId == "tenant_20"
};
