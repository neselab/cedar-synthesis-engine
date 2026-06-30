permit (
  principal is User,
  action == Action::"read",
  resource is Document
)
when {
  principal == resource.owner
};