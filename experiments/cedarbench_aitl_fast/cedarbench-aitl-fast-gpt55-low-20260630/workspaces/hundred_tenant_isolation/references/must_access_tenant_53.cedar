// Floor: a user from tenant_53 MUST be permitted to access a resource from tenant_53.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_53"
    && resource.tenantId == "tenant_53"
};
