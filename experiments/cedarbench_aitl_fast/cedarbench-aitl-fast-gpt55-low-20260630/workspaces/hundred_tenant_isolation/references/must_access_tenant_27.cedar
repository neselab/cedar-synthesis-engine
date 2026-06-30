// Floor: a user from tenant_27 MUST be permitted to access a resource from tenant_27.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_27"
    && resource.tenantId == "tenant_27"
};
