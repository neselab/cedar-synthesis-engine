// Floor: a user with cap_035 and cap_036 subscribed MUST be permitted
// to useFeature on a Feature whose required capabilities are a subset of
// {cap_035, cap_036} (and at minimum contains cap_035).
permit (
    principal is User,
    action == Action::"useFeature",
    resource is Feature
)
when {
    principal.subscribedFeatures.contains("cap_035")
    && principal.subscribedFeatures.contains("cap_036")
    && resource.requiredCapabilities.contains("cap_035")
    && ["cap_035", "cap_036"].containsAll(resource.requiredCapabilities)
};
