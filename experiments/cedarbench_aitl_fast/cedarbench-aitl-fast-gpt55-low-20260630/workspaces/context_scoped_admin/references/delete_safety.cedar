// Ceiling: delete is permitted only when the resource's tenant is in
// the principal's adminOf set. Admin powers do NOT cross tenant
// boundaries — a user with role "admin" but whose adminOf does not
// include the resource's tenant must NOT be permitted to delete.
permit (
    principal is User,
    action == Action::"delete",
    resource is Resource
)
when {
    principal.adminOf.contains(resource.tenant)
};
