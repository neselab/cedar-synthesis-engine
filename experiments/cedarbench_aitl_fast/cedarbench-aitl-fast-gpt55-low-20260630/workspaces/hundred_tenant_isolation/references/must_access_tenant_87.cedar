// Floor: a user from tenant_87 MUST be permitted to access a resource from tenant_87.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_87"
    && resource.tenantId == "tenant_87"
};
