// Floor: a user who is at least 6575 days old MUST be permitted to
// subscribe to 18+ content.
permit (
    principal is User,
    action == Action::"subscribe",
    resource is Content
)
when {
    resource.minAgeYears == 18
    && context.now.durationSince(principal.dateOfBirth) >= duration("6575d")
};
