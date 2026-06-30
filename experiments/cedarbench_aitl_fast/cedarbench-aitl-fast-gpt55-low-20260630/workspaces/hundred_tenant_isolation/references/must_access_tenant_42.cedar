// Floor: a user from tenant_42 MUST be permitted to access a resource from tenant_42.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_42"
    && resource.tenantId == "tenant_42"
};
