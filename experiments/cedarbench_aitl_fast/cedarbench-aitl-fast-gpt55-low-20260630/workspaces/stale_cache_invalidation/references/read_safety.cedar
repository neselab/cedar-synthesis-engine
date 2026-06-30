// Ceiling: read permitted only when authCacheTimestamp is present AND
// the cache is no more than 5 minutes old.
permit (
    principal is User,
    action == Action::"read",
    resource is Resource
)
when {
    context has authCacheTimestamp
    && context.now.durationSince(context.authCacheTimestamp) < duration("5m")
};
