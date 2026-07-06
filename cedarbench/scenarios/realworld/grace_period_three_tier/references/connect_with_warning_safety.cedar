// Ceiling: `connectWithWarning` is permitted ONLY in the 7-day window
// immediately before expiration (tier 2 — warning). Lower bound is
// inclusive (now >= certExpiresAt - 7d); upper bound is exclusive
// (now < certExpiresAt).
permit (
    principal is Subscriber,
    action == Action::"connectWithWarning",
    resource is Service
)
when {
    principal.certExpiresAt >= datetime("2000-01-01T00:00:00Z")
    && principal.certExpiresAt < datetime("2100-01-01T00:00:00Z")
    &&
    context.now >= principal.certExpiresAt.offset(duration("-7d"))
    && context.now < principal.certExpiresAt
};
