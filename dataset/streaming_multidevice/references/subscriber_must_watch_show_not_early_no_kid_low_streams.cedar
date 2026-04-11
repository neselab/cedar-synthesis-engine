// Floor: non-kid Subscriber MUST watch any !isEarlyAccess Show when
// activeStreams < 2.
permit (
    principal is Subscriber,
    action == Action::"watch",
    resource is Show
)
when {
    !resource.isEarlyAccess
    && !principal.profile.isKid
    && context.activeStreams < 2
};
