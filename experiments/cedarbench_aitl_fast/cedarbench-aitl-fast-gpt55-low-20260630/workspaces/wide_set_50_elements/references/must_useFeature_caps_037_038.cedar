// Floor: a user with cap_037 and cap_038 subscribed MUST be permitted
// to useFeature on a Feature whose required capabilities are a subset of
// {cap_037, cap_038} (and at minimum contains cap_037).
permit (
    principal is User,
    action == Action::"useFeature",
    resource is Feature
)
when {
    principal.subscribedFeatures.contains("cap_037")
    && principal.subscribedFeatures.contains("cap_038")
    && resource.requiredCapabilities.contains("cap_037")
    && ["cap_037", "cap_038"].containsAll(resource.requiredCapabilities)
};
