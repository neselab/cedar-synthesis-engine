// Floor: non-kid premium Subscriber with maxRating == "R" MUST watch
// early-access Show in the 24h pre-release window.
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
    && principal.profile.maxRating == "R"
};
