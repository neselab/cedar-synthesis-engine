// Floor: a user from tenant_85 MUST be permitted to access a resource from tenant_85.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_85"
    && resource.tenantId == "tenant_85"
};
