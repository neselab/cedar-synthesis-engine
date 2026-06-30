// Floor: a user with cap_013 and cap_014 subscribed MUST be permitted
// to useFeature on a Feature whose required capabilities are a subset of
// {cap_013, cap_014} (and at minimum contains cap_013).
permit (
    principal is User,
    action == Action::"useFeature",
    resource is Feature
)
when {
    principal.subscribedFeatures.contains("cap_013")
    && principal.subscribedFeatures.contains("cap_014")
    && resource.requiredCapabilities.contains("cap_013")
    && ["cap_013", "cap_014"].containsAll(resource.requiredCapabilities)
};
