// Floor: a user from tenant_36 MUST be permitted to access a resource from tenant_36.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_36"
    && resource.tenantId == "tenant_36"
};
