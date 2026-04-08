// Floor: non-kid Subscriber MUST watch any !isEarlyAccess Show when in region.
permit (
    principal is Subscriber,
    action == Action::"watch",
    resource is Show
)
when {
    !resource.isEarlyAccess
    && !principal.profile.isKid
    && resource.allowedRegions.contains(context.region)
};
