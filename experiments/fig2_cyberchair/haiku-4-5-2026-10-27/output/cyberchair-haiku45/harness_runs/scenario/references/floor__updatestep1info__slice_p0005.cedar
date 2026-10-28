permit(
  principal is User,
  action == Action::"updateStep1Info",
  resource is Submission
) when {
  ((resource.authors).contains(principal)) && (resource.step2Open)
};