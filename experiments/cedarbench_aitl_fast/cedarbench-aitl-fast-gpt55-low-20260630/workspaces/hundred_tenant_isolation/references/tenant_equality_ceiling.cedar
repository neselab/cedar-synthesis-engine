// Ceiling: access permitted only when principal.tenantId == resource.tenantId.
// A correct policy must be NO MORE PERMISSIVE than this.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.tenantId == resource.tenantId
};
