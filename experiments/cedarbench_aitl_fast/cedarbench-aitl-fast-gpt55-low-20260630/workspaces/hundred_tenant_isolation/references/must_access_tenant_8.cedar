// Floor: a user from tenant_8 MUST be permitted to access a resource from tenant_8.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_8"
    && resource.tenantId == "tenant_8"
};
