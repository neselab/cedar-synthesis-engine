// Ceiling: `connectInGrace` is permitted only in the 30-day window after
// expiration. This encoding avoids making the target inconsistent near the
// maximum Cedar datetime, where `certExpiresAt.offset(duration("30d"))`
// can overflow even though the approved early-grace floor is still satisfiable.
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
    &&
    (
        context.now < principal.certExpiresAt.offset(duration("7d"))
        ||
        (
            context.now >= principal.certExpiresAt.offset(duration("7d"))
            &&
            context.now.offset(duration("-30d")) < principal.certExpiresAt
        )
    )
};
