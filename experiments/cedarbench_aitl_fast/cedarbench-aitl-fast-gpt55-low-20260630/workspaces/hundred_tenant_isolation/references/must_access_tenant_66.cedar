// Floor: a user from tenant_66 MUST be permitted to access a resource from tenant_66.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_66"
    && resource.tenantId == "tenant_66"
};
