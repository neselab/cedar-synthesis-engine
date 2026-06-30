// Floor: a user from tenant_54 MUST be permitted to access a resource from tenant_54.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_54"
    && resource.tenantId == "tenant_54"
};
