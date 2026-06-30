// Floor: an admin MUST be permitted to edit any article (inherits editor).
permit (
    principal is User,
    action == Action::"edit",
    resource is Article
)
when {
    principal.role == "admin"
};
