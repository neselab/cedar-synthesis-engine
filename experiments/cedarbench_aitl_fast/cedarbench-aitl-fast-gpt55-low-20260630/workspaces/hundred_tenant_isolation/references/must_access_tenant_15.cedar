// Floor: a user from tenant_15 MUST be permitted to access a resource from tenant_15.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_15"
    && resource.tenantId == "tenant_15"
};
