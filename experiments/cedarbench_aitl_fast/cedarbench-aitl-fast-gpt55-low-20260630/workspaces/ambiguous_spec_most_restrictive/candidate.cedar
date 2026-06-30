permit (
    principal is User,
    action == Action::"view",
    resource is Document
)
when {
    principal.explicitGrant == true &&
    (principal.role == "admin" || principal.role == "user")
};

permit (
    principal is User,
    action == Action::"approve",
    resource is Document
)
when {
    principal.explicitGrant == true &&
    principal.role == "admin"
};