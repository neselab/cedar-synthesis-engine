// Ceiling: lock is permitted only for editor/admin.
permit (
    principal is User,
    action == Action::"lock",
    resource is Document
)
when {
    principal.role == "editor" || principal.role == "admin"
};
