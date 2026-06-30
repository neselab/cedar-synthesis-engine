// Floor: any user can view active documents.
permit (
  principal,
  action == Action::"view",
  resource
)
when {
  resource.currentStatus == Status::"active"
};
