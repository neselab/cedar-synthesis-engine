permit(
  principal is User,
  action == Action::"accessReviewerDirectory",
  resource is ReviewerDirectory
) when {
  (resource.allowedUsers).contains(principal)
};