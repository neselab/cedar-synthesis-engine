// Floor: a user from tenant_74 MUST be permitted to access a resource from tenant_74.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_74"
    && resource.tenantId == "tenant_74"
};
