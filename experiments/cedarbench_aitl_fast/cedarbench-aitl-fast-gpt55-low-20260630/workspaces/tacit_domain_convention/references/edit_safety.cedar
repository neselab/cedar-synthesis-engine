// Ceiling: edit permitted only when role is editor or admin.
// A viewer must NOT be permitted to edit.
permit (
    principal is User,
    action == Action::"edit",
    resource is Article
)
when {
    principal.role == "editor"
    || principal.role == "admin"
};
