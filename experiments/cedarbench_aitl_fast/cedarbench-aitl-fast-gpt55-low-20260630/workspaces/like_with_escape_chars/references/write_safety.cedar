// Ceiling: write is permitted only for admins, on any file.
permit (
    principal is User,
    action == Action::"write",
    resource is File
)
when {
    principal.role == "admin"
};
