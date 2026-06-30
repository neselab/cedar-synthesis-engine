// Floor: a user with cap_005 and cap_006 subscribed MUST be permitted
// to useFeature on a Feature whose required capabilities are a subset of
// {cap_005, cap_006} (and at minimum contains cap_005).
permit (
    principal is User,
    action == Action::"useFeature",
    resource is Feature
)
when {
    principal.subscribedFeatures.contains("cap_005")
    && principal.subscribedFeatures.contains("cap_006")
    && resource.requiredCapabilities.contains("cap_005")
    && ["cap_005", "cap_006"].containsAll(resource.requiredCapabilities)
};
