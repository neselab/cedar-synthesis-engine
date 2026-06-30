// Floor: a user from tenant_80 MUST be permitted to access a resource from tenant_80.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_80"
    && resource.tenantId == "tenant_80"
};
