// Floor: a user from tenant_91 MUST be permitted to access a resource from tenant_91.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_91"
    && resource.tenantId == "tenant_91"
};
