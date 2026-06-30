// Ceiling: `connectInGrace` is permitted ONLY in the 30-day window
// after expiration (tier 3 — grace). Lower bound is inclusive
// (now >= certExpiresAt); upper bound is exclusive
// (now < certExpiresAt + 30d).
permit (
    principal is Subscriber,
    action == Action::"connectInGrace",
    resource is Service
)
when {
    context.now >= principal.certExpiresAt
    && context.now < principal.certExpiresAt.offset(duration("30d"))
};
