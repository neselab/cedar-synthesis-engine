// Floor: a user from tenant_21 MUST be permitted to access a resource from tenant_21.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_21"
    && resource.tenantId == "tenant_21"
};
