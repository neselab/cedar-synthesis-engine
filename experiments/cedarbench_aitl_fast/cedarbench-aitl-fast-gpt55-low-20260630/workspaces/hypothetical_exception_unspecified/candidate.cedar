permit (
  principal is User,
  action == Action::"viewProfile",
  resource is Profile
)
when {
  principal == resource.owner
};