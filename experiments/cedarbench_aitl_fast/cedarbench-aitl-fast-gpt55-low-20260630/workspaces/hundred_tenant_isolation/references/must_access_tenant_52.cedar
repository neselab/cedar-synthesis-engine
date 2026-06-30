// Floor: a user from tenant_52 MUST be permitted to access a resource from tenant_52.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_52"
    && resource.tenantId == "tenant_52"
};
