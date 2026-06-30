// Floor: non-kid Subscriber MUST watch any !needsRentOrBuy Movie when
// in region. §8.8 exclusions: !isKid sidesteps bedtime forbid AND age
// rating forbid (both fire only for kids); allowedRegions sidesteps geo.
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
