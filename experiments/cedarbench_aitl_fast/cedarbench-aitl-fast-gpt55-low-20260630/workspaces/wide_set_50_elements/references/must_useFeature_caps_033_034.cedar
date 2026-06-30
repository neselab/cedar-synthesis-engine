// Floor: a user with cap_033 and cap_034 subscribed MUST be permitted
// to useFeature on a Feature whose required capabilities are a subset of
// {cap_033, cap_034} (and at minimum contains cap_033).
permit (
    principal is User,
    action == Action::"useFeature",
    resource is Feature
)
when {
    principal.subscribedFeatures.contains("cap_033")
    && principal.subscribedFeatures.contains("cap_034")
    && resource.requiredCapabilities.contains("cap_033")
    && ["cap_033", "cap_034"].containsAll(resource.requiredCapabilities)
};
