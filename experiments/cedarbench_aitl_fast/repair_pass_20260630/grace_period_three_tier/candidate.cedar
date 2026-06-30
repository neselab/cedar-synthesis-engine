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

permit (
    principal is Subscriber,
    action == Action::"connectWithWarning",
    resource is Service
)
when {
    principal.certExpiresAt >= datetime("2000-01-01T00:00:00Z")
    && principal.certExpiresAt < datetime("2100-01-01T00:00:00Z")
    &&
    context.now >= principal.certExpiresAt.offset(duration("-7d")) &&
    context.now < principal.certExpiresAt
};

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
