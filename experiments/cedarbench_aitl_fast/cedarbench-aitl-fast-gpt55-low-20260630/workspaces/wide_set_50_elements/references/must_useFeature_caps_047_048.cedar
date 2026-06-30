// Floor: a user with cap_047 and cap_048 subscribed MUST be permitted
// to useFeature on a Feature whose required capabilities are a subset of
// {cap_047, cap_048} (and at minimum contains cap_047).
permit (
    principal is User,
    action == Action::"useFeature",
    resource is Feature
)
when {
    principal.subscribedFeatures.contains("cap_047")
    && principal.subscribedFeatures.contains("cap_048")
    && resource.requiredCapabilities.contains("cap_047")
    && ["cap_047", "cap_048"].containsAll(resource.requiredCapabilities)
};
