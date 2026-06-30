// Floor: a user with cap_025 and cap_026 subscribed MUST be permitted
// to useFeature on a Feature whose required capabilities are a subset of
// {cap_025, cap_026} (and at minimum contains cap_025).
permit (
    principal is User,
    action == Action::"useFeature",
    resource is Feature
)
when {
    principal.subscribedFeatures.contains("cap_025")
    && principal.subscribedFeatures.contains("cap_026")
    && resource.requiredCapabilities.contains("cap_025")
    && ["cap_025", "cap_026"].containsAll(resource.requiredCapabilities)
};
