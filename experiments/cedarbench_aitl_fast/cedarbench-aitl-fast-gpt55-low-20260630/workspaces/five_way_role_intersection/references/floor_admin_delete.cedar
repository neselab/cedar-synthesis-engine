// Floor: a user in the admin role MUST be permitted to delete any
// resource. Role membership = primary role OR secondaryRoles membership.
permit (
    principal is User,
    action == Action::"delete",
    resource is Resource
)
when {
    principal.role == "admin" || principal.secondaryRoles.contains("admin")
};
