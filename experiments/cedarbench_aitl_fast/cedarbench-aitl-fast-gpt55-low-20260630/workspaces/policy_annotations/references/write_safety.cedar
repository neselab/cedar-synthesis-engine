// Ceiling: write permitted only when editor or admin.
permit (
    principal is User,
    action == Action::"write",
    resource is Article
)
when {
    principal.role == "admin"
    || principal.role == "editor"
};
