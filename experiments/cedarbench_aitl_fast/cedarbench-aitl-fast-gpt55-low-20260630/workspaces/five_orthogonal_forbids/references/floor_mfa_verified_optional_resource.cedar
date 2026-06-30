// Floor: an MFA-verified, non-blocked user accessing a non-archived,
// non-MFA-required resource during business hours and not rate-limited
// MUST be permitted (MFA being verified does not block access to
// resources that don't require it). All 5 §8.8 conditions encoded.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    !principal.isBlocked
    && principal.mfaVerified
    && !resource.isArchived
    && !resource.requiresMfa
    && !context.outsideBusinessHours
    && !context.rateLimited
};
