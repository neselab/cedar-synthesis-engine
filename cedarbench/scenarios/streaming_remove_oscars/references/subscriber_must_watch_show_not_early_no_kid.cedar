// Floor: non-kid Subscriber MUST be permitted to watch any !isEarlyAccess Show.
permit (
    principal is Subscriber,
    action == Action::"watch",
    resource is Show
)
when {
    !resource.isEarlyAccess && !principal.profile.isKid
};
