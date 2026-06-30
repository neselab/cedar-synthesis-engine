// Floor: a user from tenant_24 MUST be permitted to access a resource from tenant_24.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_24"
    && resource.tenantId == "tenant_24"
};
