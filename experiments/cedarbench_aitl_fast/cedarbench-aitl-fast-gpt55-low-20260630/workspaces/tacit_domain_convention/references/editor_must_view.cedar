// Floor: an editor MUST be permitted to view any article (inherits viewer).
permit (
    principal is User,
    action == Action::"view",
    resource is Article
)
when {
    principal.role == "editor"
};
