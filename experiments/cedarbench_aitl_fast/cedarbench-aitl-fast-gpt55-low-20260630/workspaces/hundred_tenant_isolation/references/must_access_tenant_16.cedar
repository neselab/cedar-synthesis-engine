// Floor: a user from tenant_16 MUST be permitted to access a resource from tenant_16.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_16"
    && resource.tenantId == "tenant_16"
};
