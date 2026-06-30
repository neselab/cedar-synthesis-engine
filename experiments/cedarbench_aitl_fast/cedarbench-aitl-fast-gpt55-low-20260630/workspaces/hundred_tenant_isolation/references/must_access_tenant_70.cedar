// Floor: a user from tenant_70 MUST be permitted to access a resource from tenant_70.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_70"
    && resource.tenantId == "tenant_70"
};
