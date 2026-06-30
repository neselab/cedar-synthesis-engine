// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
  principal is User,
  action == Action::"useFeature",
  resource is Feature
)
when {
  principal.subscribedFeatures.containsAll(resource.requiredCapabilities)
};
