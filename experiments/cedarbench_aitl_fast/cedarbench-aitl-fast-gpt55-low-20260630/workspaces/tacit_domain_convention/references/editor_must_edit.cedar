// Floor: an editor MUST be permitted to edit any article.
permit (
    principal is User,
    action == Action::"edit",
    resource is Article
)
when {
    principal.role == "editor"
};
