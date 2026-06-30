// Floor: a user from tenant_50 MUST be permitted to access a resource from tenant_50.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_50"
    && resource.tenantId == "tenant_50"
};
