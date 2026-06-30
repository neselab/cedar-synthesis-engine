// Floor: a user with cap_049 and cap_050 subscribed MUST be permitted
// to useFeature on a Feature whose required capabilities are a subset of
// {cap_049, cap_050} (and at minimum contains cap_049).
permit (
    principal is User,
    action == Action::"useFeature",
    resource is Feature
)
when {
    principal.subscribedFeatures.contains("cap_049")
    && principal.subscribedFeatures.contains("cap_050")
    && resource.requiredCapabilities.contains("cap_049")
    && ["cap_049", "cap_050"].containsAll(resource.requiredCapabilities)
};
