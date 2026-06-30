// Floor: service MUST append.
permit (
    principal is User,
    action == Action::"append",
    resource is AuditEntry
)
when {
    principal.role == "service"
};
