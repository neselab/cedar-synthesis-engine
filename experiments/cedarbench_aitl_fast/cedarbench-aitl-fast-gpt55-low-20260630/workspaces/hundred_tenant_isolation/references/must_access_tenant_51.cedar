// Floor: a user from tenant_51 MUST be permitted to access a resource from tenant_51.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_51"
    && resource.tenantId == "tenant_51"
};
