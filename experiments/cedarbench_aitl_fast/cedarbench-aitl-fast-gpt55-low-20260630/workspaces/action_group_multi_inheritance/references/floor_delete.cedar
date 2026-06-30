// Floor for Delete: audit-cleared admins must be able to Delete any document.
permit (
  principal,
  action == Action::"Delete",
  resource
)
when { principal.auditCleared && principal.role == "admin" };
