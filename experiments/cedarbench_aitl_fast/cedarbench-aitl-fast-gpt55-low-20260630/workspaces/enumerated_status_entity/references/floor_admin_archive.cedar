// Floor: admin can archive an active document.
permit (
  principal,
  action == Action::"archive",
  resource
)
when {
  principal.role == "admin"
  && resource.currentStatus == Status::"active"
};
