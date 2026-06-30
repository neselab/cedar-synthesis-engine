// Floor: a user from tenant_71 MUST be permitted to access a resource from tenant_71.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_71"
    && resource.tenantId == "tenant_71"
};
