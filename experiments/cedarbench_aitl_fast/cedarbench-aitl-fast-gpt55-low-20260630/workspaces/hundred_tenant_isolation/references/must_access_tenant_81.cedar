// Floor: a user from tenant_81 MUST be permitted to access a resource from tenant_81.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_81"
    && resource.tenantId == "tenant_81"
};
