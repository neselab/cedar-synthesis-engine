// Floor: a user with cap_009 and cap_010 subscribed MUST be permitted
// to useFeature on a Feature whose required capabilities are a subset of
// {cap_009, cap_010} (and at minimum contains cap_009).
permit (
    principal is User,
    action == Action::"useFeature",
    resource is Feature
)
when {
    principal.subscribedFeatures.contains("cap_009")
    && principal.subscribedFeatures.contains("cap_010")
    && resource.requiredCapabilities.contains("cap_009")
    && ["cap_009", "cap_010"].containsAll(resource.requiredCapabilities)
};
