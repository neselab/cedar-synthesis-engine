// Floor: non-kid Subscriber MUST watch any !needsRentOrBuy Movie when in region.
// Two §8.8 exclusions: !isKid sidesteps bedtime forbid; allowedRegions
// sidesteps the global geo forbid.
permit (
    principal is Subscriber,
    action == Action::"watch",
    resource is Movie
)
when {
    !resource.needsRentOrBuy
    && !principal.profile.isKid
    && resource.allowedRegions.contains(context.region)
};
