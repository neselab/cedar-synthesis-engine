// Floor: a user from tenant_93 MUST be permitted to access a resource from tenant_93.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_93"
    && resource.tenantId == "tenant_93"
};
