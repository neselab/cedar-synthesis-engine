// Ceiling: accessWithGrace is permitted ONLY when the user is still
// within the cumulative 90-day grace budget once the current session's
// elapsed time is added to the previously-consumed quota.
//
// Cedar does NOT support `+` or `-` directly on duration values, so the
// composition has to drop down to Long via duration.toMilliseconds().
//
// Sign guards are mandatory:
//   - context.now >= principal.graceStart   (else durationSince is
//     negative and the budget check is meaningless)
//   - principal.graceQuotaUsed.toMilliseconds() >= 0  (the type system
//     does not constrain duration to be non-negative)
permit (
    principal is User,
    action == Action::"accessWithGrace",
    resource is Resource
)
when {
    context.now >= principal.graceStart
    && principal.graceQuotaUsed.toMilliseconds() >= 0
    && principal.graceQuotaUsed.toMilliseconds()
       + context.now.durationSince(principal.graceStart).toMilliseconds()
       <= duration("90d").toMilliseconds()
};
