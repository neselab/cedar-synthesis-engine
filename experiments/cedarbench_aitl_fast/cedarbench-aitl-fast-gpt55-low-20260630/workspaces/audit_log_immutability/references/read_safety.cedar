// Ceiling: read only when analyst, auditor, or admin.
permit (
    principal is User,
    action == Action::"read",
    resource is AuditEntry
)
when {
    principal.role == "analyst" || principal.role == "auditor" || principal.role == "admin"
};
