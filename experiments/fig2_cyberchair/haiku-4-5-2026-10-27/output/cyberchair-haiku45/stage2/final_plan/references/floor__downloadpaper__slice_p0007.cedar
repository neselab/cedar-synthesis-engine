permit(
  principal is User,
  action == Action::"downloadPaper",
  resource is Submission
) when {
  (((resource.assignedReviewers).contains(principal)) && (resource.distributionDone)) && (!((resource.conflictedReviewers).contains(principal)))
};