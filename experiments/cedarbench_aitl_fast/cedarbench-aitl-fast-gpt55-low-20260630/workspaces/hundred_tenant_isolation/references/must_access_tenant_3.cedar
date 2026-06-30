// Floor: a user from tenant_3 MUST be permitted to access a resource from tenant_3.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_3"
    && resource.tenantId == "tenant_3"
};
