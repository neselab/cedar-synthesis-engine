// Ceiling: append only when service.
permit (
    principal is User,
    action == Action::"append",
    resource is AuditEntry
)
when {
    principal.role == "service"
};
