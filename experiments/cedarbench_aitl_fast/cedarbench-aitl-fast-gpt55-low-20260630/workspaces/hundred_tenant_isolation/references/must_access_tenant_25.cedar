// Floor: a user from tenant_25 MUST be permitted to access a resource from tenant_25.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_25"
    && resource.tenantId == "tenant_25"
};
