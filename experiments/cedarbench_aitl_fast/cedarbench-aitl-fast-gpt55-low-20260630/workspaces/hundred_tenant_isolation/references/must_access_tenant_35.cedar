// Floor: a user from tenant_35 MUST be permitted to access a resource from tenant_35.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_35"
    && resource.tenantId == "tenant_35"
};
