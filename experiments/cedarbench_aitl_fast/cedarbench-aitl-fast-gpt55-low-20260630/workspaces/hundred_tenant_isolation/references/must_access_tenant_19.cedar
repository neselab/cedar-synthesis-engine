// Floor: a user from tenant_19 MUST be permitted to access a resource from tenant_19.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_19"
    && resource.tenantId == "tenant_19"
};
