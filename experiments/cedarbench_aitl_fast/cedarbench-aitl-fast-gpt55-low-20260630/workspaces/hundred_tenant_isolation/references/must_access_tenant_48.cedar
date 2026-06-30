// Floor: a user from tenant_48 MUST be permitted to access a resource from tenant_48.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_48"
    && resource.tenantId == "tenant_48"
};
