// Floor: a user with cap_003 and cap_004 subscribed MUST be permitted
// to useFeature on a Feature whose required capabilities are a subset of
// {cap_003, cap_004} (and at minimum contains cap_003).
permit (
    principal is User,
    action == Action::"useFeature",
    resource is Feature
)
when {
    principal.subscribedFeatures.contains("cap_003")
    && principal.subscribedFeatures.contains("cap_004")
    && resource.requiredCapabilities.contains("cap_003")
    && ["cap_003", "cap_004"].containsAll(resource.requiredCapabilities)
};
