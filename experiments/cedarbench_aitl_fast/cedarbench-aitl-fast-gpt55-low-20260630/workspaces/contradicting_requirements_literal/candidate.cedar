forbid (
  principal is User,
  action == Action::"view",
  resource is Document
)
when {
  resource.quarantined
};

permit (
  principal is User,
  action == Action::"view",
  resource is Document
)
when {
  principal == resource.owner &&
  !resource.quarantined
};