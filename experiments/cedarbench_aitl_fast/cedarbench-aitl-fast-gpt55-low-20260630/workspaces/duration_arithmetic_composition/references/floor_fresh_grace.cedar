// Floor: a fresh user whose grace just started (now == graceStart) and
// who has consumed exactly 0 of the budget MUST be permitted. This is
// the simplest possible inside-budget configuration: 0 + 0 <= 90d.
permit (
    principal is User,
    action == Action::"accessWithGrace",
    resource is Resource
)
when {
    context.now == principal.graceStart
    && principal.graceQuotaUsed == duration("0d")
};
