// Floor: a user from tenant_94 MUST be permitted to access a resource from tenant_94.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_94"
    && resource.tenantId == "tenant_94"
};
