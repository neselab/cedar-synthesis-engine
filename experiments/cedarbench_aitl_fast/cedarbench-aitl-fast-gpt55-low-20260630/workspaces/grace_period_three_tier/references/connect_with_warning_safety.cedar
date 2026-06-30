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
    context.now >= principal.certExpiresAt.offset(duration("-7d"))
    && context.now < principal.certExpiresAt
};
