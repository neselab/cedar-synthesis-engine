// Floor: a User with role "admin" MUST read files matching system/*.
permit (
    principal is User,
    action == Action::"read",
    resource is File
)
when {
    principal.role == "admin"
    && resource.path like "system/*"
};
