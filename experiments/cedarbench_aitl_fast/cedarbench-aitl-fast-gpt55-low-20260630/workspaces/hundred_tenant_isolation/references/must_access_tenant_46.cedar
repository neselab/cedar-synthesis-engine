// Floor: a user from tenant_46 MUST be permitted to access a resource from tenant_46.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_46"
    && resource.tenantId == "tenant_46"
};
