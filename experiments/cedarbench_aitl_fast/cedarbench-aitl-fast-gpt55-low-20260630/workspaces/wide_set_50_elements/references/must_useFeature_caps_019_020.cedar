// Floor: a user with cap_019 and cap_020 subscribed MUST be permitted
// to useFeature on a Feature whose required capabilities are a subset of
// {cap_019, cap_020} (and at minimum contains cap_019).
permit (
    principal is User,
    action == Action::"useFeature",
    resource is Feature
)
when {
    principal.subscribedFeatures.contains("cap_019")
    && principal.subscribedFeatures.contains("cap_020")
    && resource.requiredCapabilities.contains("cap_019")
    && ["cap_019", "cap_020"].containsAll(resource.requiredCapabilities)
};
