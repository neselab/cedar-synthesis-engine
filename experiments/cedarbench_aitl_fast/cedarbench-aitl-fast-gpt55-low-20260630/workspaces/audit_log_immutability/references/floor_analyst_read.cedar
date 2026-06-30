// Floor: analyst MUST read.
permit (
    principal is User,
    action == Action::"read",
    resource is AuditEntry
)
when {
    principal.role == "analyst"
};
