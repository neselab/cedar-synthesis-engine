// Floor: Subscriber MUST be permitted to watch a Show that is past its release
// date, even if the show is flagged as early access. After releaseDate the
// early-access restriction lifts for everyone.
permit (
    principal is Subscriber,
    action == Action::"watch",
    resource is Show
)
when {
    context.now.datetime >= resource.releaseDate
};
