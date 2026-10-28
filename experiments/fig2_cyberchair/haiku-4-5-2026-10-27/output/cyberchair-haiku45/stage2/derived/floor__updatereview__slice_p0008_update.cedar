permit(
  principal is User,
  action == Action::"updateReview",
  resource is Submission
) when {
  (((resource.assignedReviewers).contains(principal)) && (!((resource.conflictedReviewers).contains(principal)))) && (resource.reviewOpen)
};