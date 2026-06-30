// Floor: a user from tenant_14 MUST be permitted to access a resource from tenant_14.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_14"
    && resource.tenantId == "tenant_14"
};
