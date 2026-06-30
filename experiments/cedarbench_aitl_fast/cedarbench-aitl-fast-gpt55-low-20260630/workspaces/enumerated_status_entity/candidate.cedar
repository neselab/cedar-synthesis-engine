permit (
  principal is User,
  action == Action::"view",
  resource is Document
)
when {
  resource.currentStatus == Status::"active"
};

permit (
  principal is User,
  action == Action::"view",
  resource is Document
)
when {
  principal.role == "admin" &&
  (resource.currentStatus == Status::"pending" ||
   resource.currentStatus == Status::"archived")
};

permit (
  principal is User,
  action == Action::"archive",
  resource is Document
)
when {
  principal.role == "admin" &&
  resource.currentStatus == Status::"active"
};

permit (
  principal is User,
  action == Action::"reactivate",
  resource is Document
)
when {
  principal.role == "admin" &&
  resource.currentStatus == Status::"archived"
};