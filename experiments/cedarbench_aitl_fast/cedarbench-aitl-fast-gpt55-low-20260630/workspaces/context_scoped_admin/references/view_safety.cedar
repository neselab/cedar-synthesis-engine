// Ceiling: view is permitted only when the resource's tenant is in the
// principal's adminOf set. Admin powers are scoped to specific tenants
// — a user with role "admin" but whose adminOf does not include the
// resource's tenant must NOT be permitted to view.
permit (
    principal is User,
    action == Action::"view",
    resource is Resource
)
when {
    principal.adminOf.contains(resource.tenant)
};
