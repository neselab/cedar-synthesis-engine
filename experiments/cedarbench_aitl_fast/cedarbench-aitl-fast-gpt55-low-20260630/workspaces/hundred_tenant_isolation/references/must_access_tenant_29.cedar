// Floor: a user from tenant_29 MUST be permitted to access a resource from tenant_29.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_29"
    && resource.tenantId == "tenant_29"
};
