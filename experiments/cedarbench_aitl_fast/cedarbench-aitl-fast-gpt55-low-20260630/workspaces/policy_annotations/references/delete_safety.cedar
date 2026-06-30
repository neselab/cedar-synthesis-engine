// Ceiling: delete permitted only when admin.
permit (
    principal is User,
    action == Action::"delete",
    resource is Article
)
when {
    principal.role == "admin"
};
