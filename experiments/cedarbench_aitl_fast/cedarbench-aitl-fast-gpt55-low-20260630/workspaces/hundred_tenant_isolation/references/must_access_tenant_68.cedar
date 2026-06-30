// Floor: a user from tenant_68 MUST be permitted to access a resource from tenant_68.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_68"
    && resource.tenantId == "tenant_68"
};
