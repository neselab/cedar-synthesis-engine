// Floor: a non-blocked, MFA-verified user accessing a non-archived,
// MFA-required resource during business hours and not rate-limited
// MUST be permitted. All 5 §8.8 disjointness conditions encoded.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    !principal.isBlocked
    && principal.mfaVerified
    && !resource.isArchived
    && resource.requiresMfa
    && !context.outsideBusinessHours
    && !context.rateLimited
};
