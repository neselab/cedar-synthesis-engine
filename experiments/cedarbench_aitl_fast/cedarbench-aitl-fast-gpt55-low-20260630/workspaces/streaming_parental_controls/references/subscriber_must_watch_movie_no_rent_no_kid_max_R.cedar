// Floor: non-kid Subscriber with maxRating == "R" MUST watch any
// !needsRentOrBuy Movie. The `maxRating == "R"` clause is the §8.8
// floor-bound consistency exclusion for the parental rating forbid:
// "R" allows all ratings, so the rating forbid never fires for these
// principals. `!isKid` is the bedtime exclusion (separate forbid).
permit (
    principal is Subscriber,
    action == Action::"watch",
    resource is Movie
)
when {
    !resource.needsRentOrBuy
    && !principal.profile.isKid
    && principal.profile.maxRating == "R"
};
