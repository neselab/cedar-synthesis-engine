// Floor: a user who is at least 4748 days old MUST be permitted to
// view 13+ content.
permit (
    principal is User,
    action == Action::"view",
    resource is Content
)
when {
    resource.minAgeYears == 13
    && context.now.durationSince(principal.dateOfBirth) >= duration("4748d")
};
