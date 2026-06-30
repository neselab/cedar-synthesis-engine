// Floor: non-kid premium Subscriber MUST watch early-access Show in 24h
// pre-release window when in region.
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
    && !principal.profile.isKid
    && resource.allowedRegions.contains(context.region)
};
