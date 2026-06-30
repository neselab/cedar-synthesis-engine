// Floor: a user from tenant_33 MUST be permitted to access a resource from tenant_33.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_33"
    && resource.tenantId == "tenant_33"
};
