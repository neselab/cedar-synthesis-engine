// Floor: an admin MUST be permitted to view any article (inherits viewer).
permit (
    principal is User,
    action == Action::"view",
    resource is Article
)
when {
    principal.role == "admin"
};
