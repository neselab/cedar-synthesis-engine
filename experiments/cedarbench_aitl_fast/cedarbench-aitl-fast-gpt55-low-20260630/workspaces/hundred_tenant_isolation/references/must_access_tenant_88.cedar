// Floor: a user from tenant_88 MUST be permitted to access a resource from tenant_88.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_88"
    && resource.tenantId == "tenant_88"
};
