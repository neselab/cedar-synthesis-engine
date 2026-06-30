// Floor: a user from tenant_58 MUST be permitted to access a resource from tenant_58.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_58"
    && resource.tenantId == "tenant_58"
};
