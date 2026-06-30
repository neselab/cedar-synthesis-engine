// Floor: an admin must be permitted to access any resource at any level.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.role == "admin"
};
