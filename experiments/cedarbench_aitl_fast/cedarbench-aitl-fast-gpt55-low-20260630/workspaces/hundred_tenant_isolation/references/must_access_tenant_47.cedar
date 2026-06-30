// Floor: a user from tenant_47 MUST be permitted to access a resource from tenant_47.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_47"
    && resource.tenantId == "tenant_47"
};
