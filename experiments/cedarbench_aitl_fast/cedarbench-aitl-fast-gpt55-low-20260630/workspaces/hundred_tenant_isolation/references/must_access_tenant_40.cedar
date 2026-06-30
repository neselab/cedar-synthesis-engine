// Floor: a user from tenant_40 MUST be permitted to access a resource from tenant_40.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_40"
    && resource.tenantId == "tenant_40"
};
