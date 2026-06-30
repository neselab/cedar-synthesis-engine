// Floor: a user with cap_001 and cap_002 subscribed MUST be permitted
// to useFeature on a Feature whose required capabilities are a subset of
// {cap_001, cap_002} (and at minimum contains cap_001).
permit (
    principal is User,
    action == Action::"useFeature",
    resource is Feature
)
when {
    principal.subscribedFeatures.contains("cap_001")
    && principal.subscribedFeatures.contains("cap_002")
    && resource.requiredCapabilities.contains("cap_001")
    && ["cap_001", "cap_002"].containsAll(resource.requiredCapabilities)
};
