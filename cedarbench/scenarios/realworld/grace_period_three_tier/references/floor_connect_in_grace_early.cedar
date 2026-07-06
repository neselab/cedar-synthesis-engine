// Floor: `connectInGrace` MUST be permitted in the early portion of the
// grace period — specifically, in the first 7 days after expiration.
// Captures the operational requirement that subscribers don't suffer
// hard-cutoff failures the instant their cert expires.
permit (
    principal is Subscriber,
    action == Action::"connectInGrace",
    resource is Service
)
when {
    principal.certExpiresAt >= datetime("2000-01-01T00:00:00Z")
    && principal.certExpiresAt < datetime("2100-01-01T00:00:00Z")
    &&
    context.now >= principal.certExpiresAt
    && context.now < principal.certExpiresAt.offset(duration("7d"))
};
