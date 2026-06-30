// Ceiling: delete permitted only for manager.
// Neither editor nor auditAdmin may delete.
permit (
    principal is Worker,
    action == Action::"delete",
    resource is Record
)
when {
    principal.role == "manager"
};
