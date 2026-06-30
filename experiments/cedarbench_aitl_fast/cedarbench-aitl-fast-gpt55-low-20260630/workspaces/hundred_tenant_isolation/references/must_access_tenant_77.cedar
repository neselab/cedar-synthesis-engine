// Floor: a user from tenant_77 MUST be permitted to access a resource from tenant_77.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_77"
    && resource.tenantId == "tenant_77"
};
