permit (
    principal is User,
    action == Action::"view",
    resource is Article
)
when {
    principal.role == "viewer" ||
    principal.role == "editor" ||
    principal.role == "admin"
};

permit (
    principal is User,
    action == Action::"edit",
    resource is Article
)
when {
    principal.role == "editor" ||
    principal.role == "admin"
};

permit (
    principal is User,
    action == Action::"delete",
    resource is Article
)
when {
    principal.role == "admin"
};