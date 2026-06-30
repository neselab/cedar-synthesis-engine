// Floor: admin can view pending and archived documents.
permit (
  principal,
  action == Action::"view",
  resource
)
when {
  principal.role == "admin"
  && (resource.currentStatus == Status::"pending" || resource.currentStatus == Status::"archived")
};
