// Floor: a user with cap_021 and cap_022 subscribed MUST be permitted
// to useFeature on a Feature whose required capabilities are a subset of
// {cap_021, cap_022} (and at minimum contains cap_021).
permit (
    principal is User,
    action == Action::"useFeature",
    resource is Feature
)
when {
    principal.subscribedFeatures.contains("cap_021")
    && principal.subscribedFeatures.contains("cap_022")
    && resource.requiredCapabilities.contains("cap_021")
    && ["cap_021", "cap_022"].containsAll(resource.requiredCapabilities)
};
