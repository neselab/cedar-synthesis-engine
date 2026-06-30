// Floor: a user from tenant_60 MUST be permitted to access a resource from tenant_60.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_60"
    && resource.tenantId == "tenant_60"
};
