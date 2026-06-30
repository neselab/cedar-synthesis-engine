// Ceiling: purchase enforces the same enumerated age thresholds as view.
permit (
    principal is User,
    action == Action::"purchase",
    resource is Content
)
when {
    (resource.minAgeYears == 13 && context.now.durationSince(principal.dateOfBirth) >= duration("4748d"))
    || (resource.minAgeYears == 18 && context.now.durationSince(principal.dateOfBirth) >= duration("6575d"))
    || (resource.minAgeYears == 21 && context.now.durationSince(principal.dateOfBirth) >= duration("7670d"))
};
