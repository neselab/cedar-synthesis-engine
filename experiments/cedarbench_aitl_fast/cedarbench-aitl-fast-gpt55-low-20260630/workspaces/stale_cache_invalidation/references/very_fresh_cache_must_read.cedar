// Floor: a fresh (< 60s) cache implies read must be permitted.
// This is a strict subset of fresh_cache_must_read, but provides an
// additional anchor at the writeCritical-bound timescale: the same
// cache that suffices for writeCritical MUST also suffice for read.
permit (
    principal is User,
    action == Action::"read",
    resource is Resource
)
when {
    context has authCacheTimestamp
    && context.now.durationSince(context.authCacheTimestamp) < duration("60s")
};
