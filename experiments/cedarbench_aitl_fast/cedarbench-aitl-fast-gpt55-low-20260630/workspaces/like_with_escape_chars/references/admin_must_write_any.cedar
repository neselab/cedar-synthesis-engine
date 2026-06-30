// Floor: a User with role "admin" MUST write any File regardless of path.
permit (
    principal is User,
    action == Action::"write",
    resource is File
)
when {
    principal.role == "admin"
};
