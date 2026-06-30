// Ceiling: writeCritical permitted only when authCacheTimestamp is
// present AND the cache is no more than 60 seconds old.
permit (
    principal is User,
    action == Action::"writeCritical",
    resource is Resource
)
when {
    context has authCacheTimestamp
    && context.now.durationSince(context.authCacheTimestamp) < duration("60s")
};
