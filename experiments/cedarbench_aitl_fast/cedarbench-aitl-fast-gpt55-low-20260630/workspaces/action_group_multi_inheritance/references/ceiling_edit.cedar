// Ceiling for Edit: AuditLogged only.
// AuditLogged requires principal.auditCleared.
permit (
  principal,
  action == Action::"Edit",
  resource
)
when { principal.auditCleared };
