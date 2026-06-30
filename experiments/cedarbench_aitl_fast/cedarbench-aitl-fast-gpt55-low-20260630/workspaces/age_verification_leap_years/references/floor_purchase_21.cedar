// Floor: a user who is at least 7670 days old MUST be permitted to
// purchase 21+ content.
permit (
    principal is User,
    action == Action::"purchase",
    resource is Content
)
when {
    resource.minAgeYears == 21
    && context.now.durationSince(principal.dateOfBirth) >= duration("7670d")
};
