// Ceiling: delete is permitted only when the principal holds the admin
// role (either as primary or in secondaryRoles). No other role grants
// delete on its own.
permit (
    principal is User,
    action == Action::"delete",
    resource is Resource
)
when {
    principal.role == "admin" || principal.secondaryRoles.contains("admin")
};
