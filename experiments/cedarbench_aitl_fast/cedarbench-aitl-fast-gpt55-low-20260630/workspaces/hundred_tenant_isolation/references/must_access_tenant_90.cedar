// Floor: a user from tenant_90 MUST be permitted to access a resource from tenant_90.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_90"
    && resource.tenantId == "tenant_90"
};
