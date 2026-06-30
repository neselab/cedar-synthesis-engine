// Floor: a user with cap_007 and cap_008 subscribed MUST be permitted
// to useFeature on a Feature whose required capabilities are a subset of
// {cap_007, cap_008} (and at minimum contains cap_007).
permit (
    principal is User,
    action == Action::"useFeature",
    resource is Feature
)
when {
    principal.subscribedFeatures.contains("cap_007")
    && principal.subscribedFeatures.contains("cap_008")
    && resource.requiredCapabilities.contains("cap_007")
    && ["cap_007", "cap_008"].containsAll(resource.requiredCapabilities)
};
