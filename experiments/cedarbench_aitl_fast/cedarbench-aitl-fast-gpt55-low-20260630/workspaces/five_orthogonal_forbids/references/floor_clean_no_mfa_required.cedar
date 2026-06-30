// Floor: a non-blocked user accessing a non-archived, non-MFA-required
// resource during business hours and not rate-limited MUST be permitted.
// All 5 §8.8 disjointness conditions are encoded explicitly.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    !principal.isBlocked
    && !resource.isArchived
    && !resource.requiresMfa
    && !context.outsideBusinessHours
    && !context.rateLimited
};
