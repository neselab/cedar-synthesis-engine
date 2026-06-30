// Floor: a user with cap_041 and cap_042 subscribed MUST be permitted
// to useFeature on a Feature whose required capabilities are a subset of
// {cap_041, cap_042} (and at minimum contains cap_041).
permit (
    principal is User,
    action == Action::"useFeature",
    resource is Feature
)
when {
    principal.subscribedFeatures.contains("cap_041")
    && principal.subscribedFeatures.contains("cap_042")
    && resource.requiredCapabilities.contains("cap_041")
    && ["cap_041", "cap_042"].containsAll(resource.requiredCapabilities)
};
