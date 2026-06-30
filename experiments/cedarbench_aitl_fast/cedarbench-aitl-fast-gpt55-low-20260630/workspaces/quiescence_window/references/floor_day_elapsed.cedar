// Floor: when the elapsed time is at least 24 hours, performAction MUST
// be permitted. Sanity bound for large windows -- catches buggy
// implementations that artificially cap the maximum elapsed time.
permit (
    principal is User,
    action == Action::"performAction",
    resource is Resource
)
when {
    context.now >= principal.lastActionAt
    && context.now.durationSince(principal.lastActionAt) >= duration("24h")
};
