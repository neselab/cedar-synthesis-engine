// Floor: a user with cap_017 and cap_018 subscribed MUST be permitted
// to useFeature on a Feature whose required capabilities are a subset of
// {cap_017, cap_018} (and at minimum contains cap_017).
permit (
    principal is User,
    action == Action::"useFeature",
    resource is Feature
)
when {
    principal.subscribedFeatures.contains("cap_017")
    && principal.subscribedFeatures.contains("cap_018")
    && resource.requiredCapabilities.contains("cap_017")
    && ["cap_017", "cap_018"].containsAll(resource.requiredCapabilities)
};
