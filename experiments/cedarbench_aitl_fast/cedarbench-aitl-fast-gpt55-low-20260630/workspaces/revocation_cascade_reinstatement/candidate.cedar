permit (
  principal is User,
  action == Action::"read",
  resource is Resource
)
when {
  principal == resource.owner
};

permit (
  principal is User,
  action == Action::"read",
  resource is Resource
)
when {
  context.accessAuthorized == true &&
  context.revocationDetected == false
};