// Ceiling: useFeature permitted only when the user's subscribed features
// contain all of the resource's required capabilities.
permit (
    principal is User,
    action == Action::"useFeature",
    resource is Feature
)
when {
    principal.subscribedFeatures.containsAll(resource.requiredCapabilities)
};
