permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == resource.tenantId
};