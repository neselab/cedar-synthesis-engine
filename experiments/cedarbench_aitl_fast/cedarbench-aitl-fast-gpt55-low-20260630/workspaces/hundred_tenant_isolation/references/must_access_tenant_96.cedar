// Floor: a user from tenant_96 MUST be permitted to access a resource from tenant_96.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_96"
    && resource.tenantId == "tenant_96"
};
