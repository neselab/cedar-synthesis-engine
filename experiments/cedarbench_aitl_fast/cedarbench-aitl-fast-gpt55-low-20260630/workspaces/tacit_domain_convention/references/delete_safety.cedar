// Ceiling: delete permitted only when role is admin.
// Viewers and editors must NOT be permitted to delete.
permit (
    principal is User,
    action == Action::"delete",
    resource is Article
)
when {
    principal.role == "admin"
};
