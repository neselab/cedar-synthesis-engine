// Floor: a user with cap_039 and cap_040 subscribed MUST be permitted
// to useFeature on a Feature whose required capabilities are a subset of
// {cap_039, cap_040} (and at minimum contains cap_039).
permit (
    principal is User,
    action == Action::"useFeature",
    resource is Feature
)
when {
    principal.subscribedFeatures.contains("cap_039")
    && principal.subscribedFeatures.contains("cap_040")
    && resource.requiredCapabilities.contains("cap_039")
    && ["cap_039", "cap_040"].containsAll(resource.requiredCapabilities)
};
