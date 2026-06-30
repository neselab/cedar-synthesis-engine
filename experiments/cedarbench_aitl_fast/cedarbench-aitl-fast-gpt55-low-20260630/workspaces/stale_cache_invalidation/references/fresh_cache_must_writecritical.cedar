// Floor: any User with a very fresh (< 60s) authCacheTimestamp MUST
// be permitted to writeCritical.
permit (
    principal is User,
    action == Action::"writeCritical",
    resource is Resource
)
when {
    context has authCacheTimestamp
    && context.now.durationSince(context.authCacheTimestamp) < duration("60s")
};
