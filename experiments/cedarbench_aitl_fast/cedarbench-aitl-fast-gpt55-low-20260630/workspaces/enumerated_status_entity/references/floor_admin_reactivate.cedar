// Floor: admin can reactivate an archived document.
permit (
  principal,
  action == Action::"reactivate",
  resource
)
when {
  principal.role == "admin"
  && resource.currentStatus == Status::"archived"
};
