// Floor: a user from tenant_49 MUST be permitted to access a resource from tenant_49.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_49"
    && resource.tenantId == "tenant_49"
};
