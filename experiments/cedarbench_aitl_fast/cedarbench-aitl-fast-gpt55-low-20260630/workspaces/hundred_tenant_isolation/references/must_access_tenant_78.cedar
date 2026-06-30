// Floor: a user from tenant_78 MUST be permitted to access a resource from tenant_78.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_78"
    && resource.tenantId == "tenant_78"
};
