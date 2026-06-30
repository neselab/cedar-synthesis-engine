// Floor: a user from tenant_63 MUST be permitted to access a resource from tenant_63.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_63"
    && resource.tenantId == "tenant_63"
};
