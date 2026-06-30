// Floor: admin MUST delete any article.
permit (
    principal is User,
    action == Action::"delete",
    resource is Article
)
when {
    principal.role == "admin"
};
