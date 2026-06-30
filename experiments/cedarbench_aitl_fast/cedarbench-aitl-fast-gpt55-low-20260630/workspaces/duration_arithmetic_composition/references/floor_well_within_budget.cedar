// Floor: any user whose previously-consumed quota PLUS the current
// session's elapsed time is at most 30 days (a third of the 90-day
// budget) MUST be permitted. Sign guards mirror the ceiling so this
// floor cannot be triggered with negative durations.
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
       <= duration("30d").toMilliseconds()
};
