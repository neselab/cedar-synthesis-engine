// Floor: non-kid Subscriber MUST watch any !needsRentOrBuy Movie when
// activeStreams < 2. The < 2 limit is the strictest tier limit (standard);
// it works for any tier including premium (which only requires < 5).
// `!isKid` is the §8.8 exclusion for the bedtime forbid; `activeStreams < 2`
// is the §8.8 exclusion for the standard-tier stream forbid (and it's
// strictly stronger than what premium requires, so it also handles premium).
permit (
    principal is Subscriber,
    action == Action::"watch",
    resource is Movie
)
when {
    !resource.needsRentOrBuy
    && !principal.profile.isKid
    && context.activeStreams < 2
};
