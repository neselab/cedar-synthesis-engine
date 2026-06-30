// Floor: an admin MUST be permitted to unlock any document.
permit (
    principal is User,
    action == Action::"unlock",
    resource is Document
)
when {
    principal.role == "admin"
};
