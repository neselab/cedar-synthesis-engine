// Ceiling: view permitted only when the user is at least the
// per-resource minimum age old, using conservative day thresholds
// that account for leap-year edge cases.
//   13 years -> 4748 days
//   18 years -> 6575 days
//   21 years -> 7670 days
permit (
    principal is User,
    action == Action::"view",
    resource is Content
)
when {
    (resource.minAgeYears == 13 && context.now.durationSince(principal.dateOfBirth) >= duration("4748d"))
    || (resource.minAgeYears == 18 && context.now.durationSince(principal.dateOfBirth) >= duration("6575d"))
    || (resource.minAgeYears == 21 && context.now.durationSince(principal.dateOfBirth) >= duration("7670d"))
};
