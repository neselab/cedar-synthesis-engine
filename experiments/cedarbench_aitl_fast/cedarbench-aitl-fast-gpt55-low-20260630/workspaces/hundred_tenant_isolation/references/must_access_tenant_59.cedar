// Floor: a user from tenant_59 MUST be permitted to access a resource from tenant_59.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_59"
    && resource.tenantId == "tenant_59"
};
