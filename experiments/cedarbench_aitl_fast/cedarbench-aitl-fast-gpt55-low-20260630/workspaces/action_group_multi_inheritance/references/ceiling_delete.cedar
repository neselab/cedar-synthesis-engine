// Ceiling for Delete: AuditLogged + Destructive.
// AuditLogged requires principal.auditCleared.
// Destructive requires principal.role == "admin".
permit (
  principal,
  action == Action::"Delete",
  resource
)
when { principal.auditCleared && principal.role == "admin" };
