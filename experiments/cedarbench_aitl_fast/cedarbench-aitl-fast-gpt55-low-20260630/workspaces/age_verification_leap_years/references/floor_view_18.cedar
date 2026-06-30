// Floor: a user who is at least 6575 days old MUST be permitted to
// view 18+ content. (6575 days = 18*365 + 5 leap days, the conservative
// threshold that guarantees the user has had their 18th birthday in
// any plausible leap-year alignment.)
permit (
    principal is User,
    action == Action::"view",
    resource is Content
)
when {
    resource.minAgeYears == 18
    && context.now.durationSince(principal.dateOfBirth) >= duration("6575d")
};
