// Floor: a user from tenant_56 MUST be permitted to access a resource from tenant_56.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_56"
    && resource.tenantId == "tenant_56"
};
