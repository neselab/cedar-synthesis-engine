// Floor: a user from tenant_65 MUST be permitted to access a resource from tenant_65.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_65"
    && resource.tenantId == "tenant_65"
};
