// Floor: a user from tenant_44 MUST be permitted to access a resource from tenant_44.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_44"
    && resource.tenantId == "tenant_44"
};
