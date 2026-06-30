// Floor: a user from tenant_55 MUST be permitted to access a resource from tenant_55.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_55"
    && resource.tenantId == "tenant_55"
};
