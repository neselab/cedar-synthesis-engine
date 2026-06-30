// Floor: a user from tenant_92 MUST be permitted to access a resource from tenant_92.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_92"
    && resource.tenantId == "tenant_92"
};
