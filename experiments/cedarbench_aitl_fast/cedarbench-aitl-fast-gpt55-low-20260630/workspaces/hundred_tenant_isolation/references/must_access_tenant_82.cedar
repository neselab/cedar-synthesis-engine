// Floor: a user from tenant_82 MUST be permitted to access a resource from tenant_82.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_82"
    && resource.tenantId == "tenant_82"
};
