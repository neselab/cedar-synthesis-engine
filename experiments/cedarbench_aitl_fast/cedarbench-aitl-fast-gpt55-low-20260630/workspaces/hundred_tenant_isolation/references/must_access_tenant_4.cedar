// Floor: a user from tenant_4 MUST be permitted to access a resource from tenant_4.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_4"
    && resource.tenantId == "tenant_4"
};
