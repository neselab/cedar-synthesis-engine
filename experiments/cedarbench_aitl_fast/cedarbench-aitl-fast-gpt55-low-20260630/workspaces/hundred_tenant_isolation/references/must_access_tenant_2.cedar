// Floor: a user from tenant_2 MUST be permitted to access a resource from tenant_2.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_2"
    && resource.tenantId == "tenant_2"
};
