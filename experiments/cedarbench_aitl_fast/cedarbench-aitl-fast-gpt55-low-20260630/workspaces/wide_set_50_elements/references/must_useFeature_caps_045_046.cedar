// Floor: a user with cap_045 and cap_046 subscribed MUST be permitted
// to useFeature on a Feature whose required capabilities are a subset of
// {cap_045, cap_046} (and at minimum contains cap_045).
permit (
    principal is User,
    action == Action::"useFeature",
    resource is Feature
)
when {
    principal.subscribedFeatures.contains("cap_045")
    && principal.subscribedFeatures.contains("cap_046")
    && resource.requiredCapabilities.contains("cap_045")
    && ["cap_045", "cap_046"].containsAll(resource.requiredCapabilities)
};
