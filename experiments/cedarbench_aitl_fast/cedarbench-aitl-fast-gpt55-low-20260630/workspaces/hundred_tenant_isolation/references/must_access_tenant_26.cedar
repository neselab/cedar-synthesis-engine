// Floor: a user from tenant_26 MUST be permitted to access a resource from tenant_26.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_26"
    && resource.tenantId == "tenant_26"
};
