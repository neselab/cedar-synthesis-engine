// Floor: a user from tenant_34 MUST be permitted to access a resource from tenant_34.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_34"
    && resource.tenantId == "tenant_34"
};
