// Floor: a user from tenant_83 MUST be permitted to access a resource from tenant_83.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_83"
    && resource.tenantId == "tenant_83"
};
