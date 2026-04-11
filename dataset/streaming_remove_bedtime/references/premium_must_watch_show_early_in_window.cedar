// Floor: a premium-tier Subscriber MUST be permitted to watch a Show in early
// access if the current time is within the 24-hour window before releaseDate.
permit (
    principal is Subscriber,
    action == Action::"watch",
    resource is Show
)
when {
    resource.isEarlyAccess
    && principal.subscription.tier == "premium"
    && context.now.datetime >= resource.releaseDate.offset(duration("-24h"))
    && context.now.datetime < resource.releaseDate
};
