// Floor: a user from tenant_23 MUST be permitted to access a resource from tenant_23.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_23"
    && resource.tenantId == "tenant_23"
};
