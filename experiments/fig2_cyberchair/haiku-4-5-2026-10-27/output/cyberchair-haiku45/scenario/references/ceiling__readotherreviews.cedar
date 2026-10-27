permit(
  principal is User,
  action == Action::"readOtherReviews",
  resource is Submission
) when {
  (resource.reviewersSubmitted).contains(principal)
};