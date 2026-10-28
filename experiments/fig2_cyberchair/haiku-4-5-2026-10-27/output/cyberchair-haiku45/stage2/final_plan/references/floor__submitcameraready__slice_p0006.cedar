permit(
  principal is User,
  action == Action::"submitCameraReady",
  resource is Submission
) when {
  (((resource.authors).contains(principal)) && (resource.selected)) && (resource.reviewProcessDone)
};