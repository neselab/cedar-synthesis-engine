// Floor: a user from tenant_69 MUST be permitted to access a resource from tenant_69.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_69"
    && resource.tenantId == "tenant_69"
};
