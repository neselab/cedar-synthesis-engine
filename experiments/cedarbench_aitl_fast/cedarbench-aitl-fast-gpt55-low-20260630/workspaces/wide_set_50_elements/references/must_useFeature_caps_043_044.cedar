// Floor: a user with cap_043 and cap_044 subscribed MUST be permitted
// to useFeature on a Feature whose required capabilities are a subset of
// {cap_043, cap_044} (and at minimum contains cap_043).
permit (
    principal is User,
    action == Action::"useFeature",
    resource is Feature
)
when {
    principal.subscribedFeatures.contains("cap_043")
    && principal.subscribedFeatures.contains("cap_044")
    && resource.requiredCapabilities.contains("cap_043")
    && ["cap_043", "cap_044"].containsAll(resource.requiredCapabilities)
};
