// Floor: a user from tenant_32 MUST be permitted to access a resource from tenant_32.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_32"
    && resource.tenantId == "tenant_32"
};
