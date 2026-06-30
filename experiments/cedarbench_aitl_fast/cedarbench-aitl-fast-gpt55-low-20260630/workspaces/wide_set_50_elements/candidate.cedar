permit (
  principal is User,
  action == Action::"useFeature",
  resource is Feature
)
when {
  principal.subscribedFeatures.containsAll(resource.requiredCapabilities)
};