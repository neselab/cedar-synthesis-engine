permit(
  principal is User,
  action == Action::"submitReview",
  resource is Submission
) when {
  (((resource.assignedReviewers).contains(principal)) && (!((resource.conflictedReviewers).contains(principal)))) && (resource.reviewOpen)
};