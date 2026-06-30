// Floor: a user from tenant_5 MUST be permitted to access a resource from tenant_5.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_5"
    && resource.tenantId == "tenant_5"
};
