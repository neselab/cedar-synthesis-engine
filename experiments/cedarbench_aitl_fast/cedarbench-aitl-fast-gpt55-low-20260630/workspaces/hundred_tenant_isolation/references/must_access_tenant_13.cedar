// Floor: a user from tenant_13 MUST be permitted to access a resource from tenant_13.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_13"
    && resource.tenantId == "tenant_13"
};
