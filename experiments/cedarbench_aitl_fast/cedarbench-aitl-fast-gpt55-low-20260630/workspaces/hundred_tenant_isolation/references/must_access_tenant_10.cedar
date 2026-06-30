// Floor: a user from tenant_10 MUST be permitted to access a resource from tenant_10.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_10"
    && resource.tenantId == "tenant_10"
};
