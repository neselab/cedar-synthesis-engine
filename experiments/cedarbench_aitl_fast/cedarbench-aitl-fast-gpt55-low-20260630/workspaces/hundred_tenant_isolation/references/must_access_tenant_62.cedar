// Floor: a user from tenant_62 MUST be permitted to access a resource from tenant_62.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_62"
    && resource.tenantId == "tenant_62"
};
