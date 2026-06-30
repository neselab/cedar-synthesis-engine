permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
};

forbid (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    principal.role != "admin" &&
    !(principal.role == "user" && resource.level <= 3)
};