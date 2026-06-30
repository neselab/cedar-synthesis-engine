// Floor: a user from tenant_76 MUST be permitted to access a resource from tenant_76.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_76"
    && resource.tenantId == "tenant_76"
};
