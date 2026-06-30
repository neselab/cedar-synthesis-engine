// Floor: any User with a fresh (< 5m) authCacheTimestamp MUST be
// permitted to read.
permit (
    principal is User,
    action == Action::"read",
    resource is Resource
)
when {
    context has authCacheTimestamp
    && context.now.durationSince(context.authCacheTimestamp) < duration("5m")
};
