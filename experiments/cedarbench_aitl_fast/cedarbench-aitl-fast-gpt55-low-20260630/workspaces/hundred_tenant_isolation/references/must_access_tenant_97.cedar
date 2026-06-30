// Floor: a user from tenant_97 MUST be permitted to access a resource from tenant_97.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_97"
    && resource.tenantId == "tenant_97"
};
