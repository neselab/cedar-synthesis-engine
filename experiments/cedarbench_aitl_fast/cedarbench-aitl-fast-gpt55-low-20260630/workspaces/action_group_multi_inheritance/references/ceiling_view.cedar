// Ceiling for View: ReadOnly + AuditLogged.
// AuditLogged requires principal.auditCleared.
permit (
  principal,
  action == Action::"View",
  resource
)
when { principal.auditCleared };
