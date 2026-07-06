// Floor: `connectWithWarning` MUST be permitted in the 7-day window
// immediately before expiration (tier 2 — warning). Required so that
// subscribers receive renewal warnings rather than being silently locked
// out at the threshold.
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
