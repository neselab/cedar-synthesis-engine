// Floor: a user with cap_029 and cap_030 subscribed MUST be permitted
// to useFeature on a Feature whose required capabilities are a subset of
// {cap_029, cap_030} (and at minimum contains cap_029).
permit (
    principal is User,
    action == Action::"useFeature",
    resource is Feature
)
when {
    principal.subscribedFeatures.contains("cap_029")
    && principal.subscribedFeatures.contains("cap_030")
    && resource.requiredCapabilities.contains("cap_029")
    && ["cap_029", "cap_030"].containsAll(resource.requiredCapabilities)
};
