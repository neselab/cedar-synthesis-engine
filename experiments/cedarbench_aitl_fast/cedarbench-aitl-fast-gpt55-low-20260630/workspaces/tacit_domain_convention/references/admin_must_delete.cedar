// Floor: an admin MUST be permitted to delete any article.
permit (
    principal is User,
    action == Action::"delete",
    resource is Article
)
when {
    principal.role == "admin"
};
