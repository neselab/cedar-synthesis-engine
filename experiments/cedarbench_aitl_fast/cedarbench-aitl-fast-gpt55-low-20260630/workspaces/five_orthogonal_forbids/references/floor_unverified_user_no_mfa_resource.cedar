// Floor: a non-blocked user WITHOUT MFA verification accessing a
// non-archived, non-MFA-required resource during business hours and not
// rate-limited MUST be permitted (lack of MFA only matters when the
// resource requires it). All 5 §8.8 conditions encoded.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    !principal.isBlocked
    && !principal.mfaVerified
    && !resource.isArchived
    && !resource.requiresMfa
    && !context.outsideBusinessHours
    && !context.rateLimited
};
