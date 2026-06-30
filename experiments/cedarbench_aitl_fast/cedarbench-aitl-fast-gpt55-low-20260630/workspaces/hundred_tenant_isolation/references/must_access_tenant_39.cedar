// Floor: a user from tenant_39 MUST be permitted to access a resource from tenant_39.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_39"
    && resource.tenantId == "tenant_39"
};
