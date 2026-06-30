// Ceiling for view: only allowed if (status == active) OR (admin AND status in {pending, archived}).
permit (
  principal,
  action == Action::"view",
  resource
)
when {
  resource.currentStatus == Status::"active"
  ||
  (
    principal.role == "admin"
    &&
    (resource.currentStatus == Status::"pending" || resource.currentStatus == Status::"archived")
  )
};
