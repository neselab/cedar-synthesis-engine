// Floor for View: audit-cleared users must be able to View any document.
permit (
  principal,
  action == Action::"View",
  resource
)
when { principal.auditCleared };
