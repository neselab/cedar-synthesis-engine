// Ceiling for archive: only admin, only on active docs.
permit (
  principal,
  action == Action::"archive",
  resource
)
when {
  principal.role == "admin"
  && resource.currentStatus == Status::"active"
};
