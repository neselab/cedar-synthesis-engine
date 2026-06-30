permit (
  principal is User,
  action == Action::"append",
  resource is AuditEntry
)
when {
  principal.role == "service"
};

permit (
  principal is User,
  action == Action::"read",
  resource is AuditEntry
)
when {
  principal.role == "analyst" ||
  principal.role == "auditor" ||
  principal.role == "admin"
};

permit (
  principal is User,
  action == Action::"export",
  resource is AuditEntry
)
when {
  principal.role == "auditor"
};

forbid (
  principal is User,
  action == Action::"delete",
  resource is AuditEntry
);

forbid (
  principal is User,
  action == Action::"modify",
  resource is AuditEntry
);