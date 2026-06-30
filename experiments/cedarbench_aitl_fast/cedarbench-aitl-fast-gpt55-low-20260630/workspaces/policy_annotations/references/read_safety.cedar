// Ceiling: read permitted only when viewer+published, editor, or admin.
permit (
    principal is User,
    action == Action::"read",
    resource is Article
)
when {
    principal.role == "admin"
    || principal.role == "editor"
    || (principal.role == "viewer" && resource.isPublished)
};
