// Floor: a user from tenant_11 MUST be permitted to access a resource from tenant_11.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_11"
    && resource.tenantId == "tenant_11"
};
