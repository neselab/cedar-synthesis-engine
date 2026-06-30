// Floor: a user from tenant_79 MUST be permitted to access a resource from tenant_79.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_79"
    && resource.tenantId == "tenant_79"
};
