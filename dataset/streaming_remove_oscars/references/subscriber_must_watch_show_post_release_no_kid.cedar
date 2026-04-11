// Floor: non-kid Subscriber MUST be permitted to watch a Show that is past
// its releaseDate (early-access lifts after release).
permit (
    principal is Subscriber,
    action == Action::"watch",
    resource is Show
)
when {
    context.now.datetime >= resource.releaseDate && !principal.profile.isKid
};
