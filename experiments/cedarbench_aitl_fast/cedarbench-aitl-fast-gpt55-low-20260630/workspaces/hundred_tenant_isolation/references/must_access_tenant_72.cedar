// Floor: a user from tenant_72 MUST be permitted to access a resource from tenant_72.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_72"
    && resource.tenantId == "tenant_72"
};
