permit (
  principal is User,
  action == Action::"view",
  resource is Document
);

forbid (
  principal is User,
  action == Action::"view",
  resource is Document
)
when {
  resource.archived
}
unless {
  principal == resource.owner
};

permit (
  principal is User,
  action == Action::"edit",
  resource is Document
)
when {
  principal == resource.owner
};

forbid (
  principal is User,
  action == Action::"edit",
  resource is Document
)
when {
  resource.archived
};