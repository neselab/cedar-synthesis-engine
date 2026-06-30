// Floor: a user from tenant_73 MUST be permitted to access a resource from tenant_73.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_73"
    && resource.tenantId == "tenant_73"
};
