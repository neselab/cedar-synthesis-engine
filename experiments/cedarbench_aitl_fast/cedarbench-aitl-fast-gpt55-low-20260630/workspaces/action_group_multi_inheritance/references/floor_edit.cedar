// Floor for Edit: audit-cleared users must be able to Edit any document.
permit (
  principal,
  action == Action::"Edit",
  resource
)
when { principal.auditCleared };
