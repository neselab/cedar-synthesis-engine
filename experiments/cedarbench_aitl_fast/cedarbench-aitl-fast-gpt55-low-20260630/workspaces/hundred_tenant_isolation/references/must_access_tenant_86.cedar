// Floor: a user from tenant_86 MUST be permitted to access a resource from tenant_86.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_86"
    && resource.tenantId == "tenant_86"
};
