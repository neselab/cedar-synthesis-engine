// Floor: a user from tenant_28 MUST be permitted to access a resource from tenant_28.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_28"
    && resource.tenantId == "tenant_28"
};
