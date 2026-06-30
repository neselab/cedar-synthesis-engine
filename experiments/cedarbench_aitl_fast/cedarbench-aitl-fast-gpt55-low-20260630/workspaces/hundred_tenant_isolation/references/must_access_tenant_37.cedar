// Floor: a user from tenant_37 MUST be permitted to access a resource from tenant_37.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_37"
    && resource.tenantId == "tenant_37"
};
