// Floor: a user with cap_023 and cap_024 subscribed MUST be permitted
// to useFeature on a Feature whose required capabilities are a subset of
// {cap_023, cap_024} (and at minimum contains cap_023).
permit (
    principal is User,
    action == Action::"useFeature",
    resource is Feature
)
when {
    principal.subscribedFeatures.contains("cap_023")
    && principal.subscribedFeatures.contains("cap_024")
    && resource.requiredCapabilities.contains("cap_023")
    && ["cap_023", "cap_024"].containsAll(resource.requiredCapabilities)
};
