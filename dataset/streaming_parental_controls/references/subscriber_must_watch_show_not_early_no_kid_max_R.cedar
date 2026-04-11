// Floor: non-kid Subscriber with maxRating == "R" MUST watch any
// !isEarlyAccess Show.
permit (
    principal is Subscriber,
    action == Action::"watch",
    resource is Show
)
when {
    !resource.isEarlyAccess
    && !principal.profile.isKid
    && principal.profile.maxRating == "R"
};
