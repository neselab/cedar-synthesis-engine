permit(
  principal is User,
  action == Action::"monitorReviewProcess",
  resource is ReviewOverview
) when {
  ((principal.role) == "Chair") || ((principal.role) == "PCC")
};