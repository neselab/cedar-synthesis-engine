permit(
  principal is User,
  action == Action::"submitFullPaper",
  resource is Submission
) when {
  (((resource.authors).contains(principal)) && (context.hasStep2Credential)) && (resource.step2Open)
};