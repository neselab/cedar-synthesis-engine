permit(
  principal is User,
  action == Action::"volunteerForConflictingPaper",
  resource is Submission
) when {
  (((principal.role) == "Reviewer") && (principal.submittedAllAssignedReviews)) && (!((resource.conflictedReviewers).contains(principal)))
};