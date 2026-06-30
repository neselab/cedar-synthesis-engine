// Floor: a user with cap_027 and cap_028 subscribed MUST be permitted
// to useFeature on a Feature whose required capabilities are a subset of
// {cap_027, cap_028} (and at minimum contains cap_027).
permit (
    principal is User,
    action == Action::"useFeature",
    resource is Feature
)
when {
    principal.subscribedFeatures.contains("cap_027")
    && principal.subscribedFeatures.contains("cap_028")
    && resource.requiredCapabilities.contains("cap_027")
    && ["cap_027", "cap_028"].containsAll(resource.requiredCapabilities)
};
