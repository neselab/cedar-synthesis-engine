// Floor: editor MUST write any article.
permit (
    principal is User,
    action == Action::"write",
    resource is Article
)
when {
    principal.role == "editor"
};
