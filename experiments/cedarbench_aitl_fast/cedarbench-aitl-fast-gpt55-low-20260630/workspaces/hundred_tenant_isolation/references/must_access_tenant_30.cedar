// Floor: a user from tenant_30 MUST be permitted to access a resource from tenant_30.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_30"
    && resource.tenantId == "tenant_30"
};
