// Floor: a user from tenant_84 MUST be permitted to access a resource from tenant_84.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_84"
    && resource.tenantId == "tenant_84"
};
