// Floor: a user from tenant_43 MUST be permitted to access a resource from tenant_43.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == "tenant_43"
    && resource.tenantId == "tenant_43"
};
