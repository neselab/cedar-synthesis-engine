// Floor: a user from tenant_61 MUST be permitted to access a resource from tenant_61.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_61"
    && resource.tenantId == "tenant_61"
};
