// Floor: any Subscriber MUST be permitted to watch any Movie that does not
// require rent-or-buy, AS LONG AS the kid profile is not enabled.
//
// The `!principal.profile.isKid` clause is the §8.8 floor-bound consistency
// exclusion: it ensures the floor's permitted set is disjoint from the
// kid-bedtime forbid's denied set. Without it, the floor would promise
// permission for kid-profile subscribers in the bedtime window, which the
// global bedtime forbid would deny — making the bounds jointly unsatisfiable.
permit (
    principal is Subscriber,
    action == Action::"watch",
    resource is Movie
)
when {
    !resource.needsRentOrBuy && !principal.profile.isKid
};
