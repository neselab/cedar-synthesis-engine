// Ceiling: `connect` (normal connection) is permitted ONLY when the
// current time is more than 7 days before the certificate's expiration
// (tier 1 — pre-warning). Equivalently: now < certExpiresAt - 7d, which
// in Cedar's offset arithmetic is `now < certExpiresAt.offset(duration("-7d"))`.
permit (
    principal is Subscriber,
    action == Action::"connect",
    resource is Service
)
when {
    principal.certExpiresAt >= datetime("2000-01-01T00:00:00Z")
    && principal.certExpiresAt < datetime("2100-01-01T00:00:00Z")
    &&
    context.now < principal.certExpiresAt.offset(duration("-7d"))
};
