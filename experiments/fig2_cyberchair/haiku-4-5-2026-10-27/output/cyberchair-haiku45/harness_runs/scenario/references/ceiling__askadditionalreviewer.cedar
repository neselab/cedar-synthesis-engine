permit(
  principal is User,
  action == Action::"askAdditionalReviewer",
  resource is ReviewOverview
) when {
  ((principal.role) == "PCC") && (((resource.paper).onlyNonExpertReviews) == true)
};