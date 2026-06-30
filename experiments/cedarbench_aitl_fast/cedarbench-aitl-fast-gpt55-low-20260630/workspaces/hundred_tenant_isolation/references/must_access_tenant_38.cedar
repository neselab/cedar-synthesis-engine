// Floor: a user from tenant_38 MUST be permitted to access a resource from tenant_38.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_38"
    && resource.tenantId == "tenant_38"
};
