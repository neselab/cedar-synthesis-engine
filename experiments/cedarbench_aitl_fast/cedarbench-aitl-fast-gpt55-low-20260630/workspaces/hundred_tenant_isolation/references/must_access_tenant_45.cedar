// Floor: a user from tenant_45 MUST be permitted to access a resource from tenant_45.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_45"
    && resource.tenantId == "tenant_45"
};
