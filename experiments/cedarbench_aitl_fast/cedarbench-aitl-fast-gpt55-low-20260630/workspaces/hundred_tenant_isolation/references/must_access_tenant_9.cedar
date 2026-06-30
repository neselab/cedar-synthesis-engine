// Floor: a user from tenant_9 MUST be permitted to access a resource from tenant_9.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_9"
    && resource.tenantId == "tenant_9"
};
