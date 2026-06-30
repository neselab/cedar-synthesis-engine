// Floor: a user from tenant_31 MUST be permitted to access a resource from tenant_31.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_31"
    && resource.tenantId == "tenant_31"
};
