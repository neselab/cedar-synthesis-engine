// Floor: a user from tenant_22 MUST be permitted to access a resource from tenant_22.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_22"
    && resource.tenantId == "tenant_22"
};
