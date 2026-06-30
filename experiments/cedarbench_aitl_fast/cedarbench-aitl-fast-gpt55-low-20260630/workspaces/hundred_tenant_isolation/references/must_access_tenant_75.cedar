// Floor: a user from tenant_75 MUST be permitted to access a resource from tenant_75.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_75"
    && resource.tenantId == "tenant_75"
};
