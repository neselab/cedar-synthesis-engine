// Floor: a user from tenant_7 MUST be permitted to access a resource from tenant_7.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_7"
    && resource.tenantId == "tenant_7"
};
