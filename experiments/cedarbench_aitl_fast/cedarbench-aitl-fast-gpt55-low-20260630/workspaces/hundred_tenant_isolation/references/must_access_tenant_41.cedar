// Floor: a user from tenant_41 MUST be permitted to access a resource from tenant_41.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_41"
    && resource.tenantId == "tenant_41"
};
