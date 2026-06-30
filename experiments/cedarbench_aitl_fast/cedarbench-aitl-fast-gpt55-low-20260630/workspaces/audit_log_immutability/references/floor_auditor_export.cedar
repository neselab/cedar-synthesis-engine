// Floor: auditor MUST export.
permit (
    principal is User,
    action == Action::"export",
    resource is AuditEntry
)
when {
    principal.role == "auditor"
};
