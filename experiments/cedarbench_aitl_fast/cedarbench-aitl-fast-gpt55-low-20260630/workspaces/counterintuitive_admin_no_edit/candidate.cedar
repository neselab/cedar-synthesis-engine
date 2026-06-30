permit (
  principal is Worker,
  action == Action::"view",
  resource is Record
)
when {
  principal.role == "editor" ||
  principal.role == "manager" ||
  principal.role == "auditAdmin"
};

permit (
  principal is Worker,
  action == Action::"edit",
  resource is Record
)
when {
  principal.role == "editor" ||
  principal.role == "manager"
};

permit (
  principal is Worker,
  action == Action::"delete",
  resource is Record
)
when {
  principal.role == "manager"
};