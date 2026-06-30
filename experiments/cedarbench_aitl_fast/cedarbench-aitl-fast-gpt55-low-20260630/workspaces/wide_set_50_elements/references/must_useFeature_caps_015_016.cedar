// Floor: a user with cap_015 and cap_016 subscribed MUST be permitted
// to useFeature on a Feature whose required capabilities are a subset of
// {cap_015, cap_016} (and at minimum contains cap_015).
permit (
    principal is User,
    action == Action::"useFeature",
    resource is Feature
)
when {
    principal.subscribedFeatures.contains("cap_015")
    && principal.subscribedFeatures.contains("cap_016")
    && resource.requiredCapabilities.contains("cap_015")
    && ["cap_015", "cap_016"].containsAll(resource.requiredCapabilities)
};
