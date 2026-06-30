// Ceiling for reactivate: only admin, only on archived docs.
permit (
  principal,
  action == Action::"reactivate",
  resource
)
when {
  principal.role == "admin"
  && resource.currentStatus == Status::"archived"
};
