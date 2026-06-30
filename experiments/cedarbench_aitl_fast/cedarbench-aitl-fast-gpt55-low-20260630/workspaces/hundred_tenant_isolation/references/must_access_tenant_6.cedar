// Floor: a user from tenant_6 MUST be permitted to access a resource from tenant_6.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_6"
    && resource.tenantId == "tenant_6"
};
