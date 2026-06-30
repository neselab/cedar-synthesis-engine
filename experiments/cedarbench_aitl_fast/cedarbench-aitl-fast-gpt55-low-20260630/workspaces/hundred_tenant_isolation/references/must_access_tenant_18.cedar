// Floor: a user from tenant_18 MUST be permitted to access a resource from tenant_18.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_18"
    && resource.tenantId == "tenant_18"
};
