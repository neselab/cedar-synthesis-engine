// Floor: a user with cap_031 and cap_032 subscribed MUST be permitted
// to useFeature on a Feature whose required capabilities are a subset of
// {cap_031, cap_032} (and at minimum contains cap_031).
permit (
    principal is User,
    action == Action::"useFeature",
    resource is Feature
)
when {
    principal.subscribedFeatures.contains("cap_031")
    && principal.subscribedFeatures.contains("cap_032")
    && resource.requiredCapabilities.contains("cap_031")
    && ["cap_031", "cap_032"].containsAll(resource.requiredCapabilities)
};
