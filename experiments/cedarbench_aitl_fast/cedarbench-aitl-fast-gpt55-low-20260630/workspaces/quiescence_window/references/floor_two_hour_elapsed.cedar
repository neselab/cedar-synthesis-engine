// Floor: when the elapsed time is at least 2 hours (well past the
// 1-hour cooldown), performAction MUST be permitted.
//
// The candidate must be AT LEAST as permissive as this floor on this slice.
permit (
    principal is User,
    action == Action::"performAction",
    resource is Resource
)
when {
    context.now >= principal.lastActionAt
    && context.now.durationSince(principal.lastActionAt) >= duration("2h")
};
