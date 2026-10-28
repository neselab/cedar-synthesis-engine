permit(
  principal is User,
  action == Action::"readReviewFile",
  resource is ReviewFile
) when {
  ((resource.directory).allowedUsers).contains(principal)
};