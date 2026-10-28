permit(
  principal is User,
  action == Action::"declareConflict",
  resource is Submission
) when {
  (resource.assignedReviewers).contains(principal)
};