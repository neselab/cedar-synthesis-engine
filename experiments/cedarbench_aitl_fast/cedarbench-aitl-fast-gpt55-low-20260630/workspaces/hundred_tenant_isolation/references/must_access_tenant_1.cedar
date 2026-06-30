// Floor: a user from tenant_1 MUST be permitted to access a resource from tenant_1.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_1"
    && resource.tenantId == "tenant_1"
};
