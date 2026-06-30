// FLOOR_ADMIN for `write`.
permit (
    principal is User,
    action == Action::"write",
    resource is Resource
)
when {
    principal.role == "admin"
};
