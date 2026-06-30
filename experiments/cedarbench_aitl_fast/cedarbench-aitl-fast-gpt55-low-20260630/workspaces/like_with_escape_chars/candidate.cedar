permit (
    principal is User,
    action == Action::"read",
    resource is File
)
when {
    resource.path like "docs/*"
};

permit (
    principal is User,
    action == Action::"read",
    resource is File
)
when {
    principal.role == "user" &&
    resource.path like "reports/*\*-final"
};

permit (
    principal is User,
    action == Action::"read",
    resource is File
)
when {
    principal.role == "admin" &&
    resource.path like "system/*"
};

permit (
    principal is User,
    action == Action::"write",
    resource is File
)
when {
    principal.role == "admin"
};