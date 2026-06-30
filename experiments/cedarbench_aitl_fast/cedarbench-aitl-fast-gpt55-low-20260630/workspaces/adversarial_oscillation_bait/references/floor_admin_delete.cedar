// FLOOR_ADMIN for `delete`.
permit (
    principal is User,
    action == Action::"delete",
    resource is Resource
)
when {
    principal.role == "admin"
};
