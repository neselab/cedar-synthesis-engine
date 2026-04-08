// Floor: non-kid Subscriber MUST be permitted to watch any !needsRentOrBuy Movie.
// `!principal.profile.isKid` is the §8.8 floor-bound consistency exclusion:
// it makes the floor's permitted set disjoint from the kid-bedtime forbid.
permit (
    principal is Subscriber,
    action == Action::"watch",
    resource is Movie
)
when {
    !resource.needsRentOrBuy && !principal.profile.isKid
};
