// Floor: a user with cap_011 and cap_012 subscribed MUST be permitted
// to useFeature on a Feature whose required capabilities are a subset of
// {cap_011, cap_012} (and at minimum contains cap_011).
permit (
    principal is User,
    action == Action::"useFeature",
    resource is Feature
)
when {
    principal.subscribedFeatures.contains("cap_011")
    && principal.subscribedFeatures.contains("cap_012")
    && resource.requiredCapabilities.contains("cap_011")
    && ["cap_011", "cap_012"].containsAll(resource.requiredCapabilities)
};
