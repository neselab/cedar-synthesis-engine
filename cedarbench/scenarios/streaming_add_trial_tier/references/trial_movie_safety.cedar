// Ceiling: a TrialMember may watch a Movie only when at least one of:
//  (a) the movie is free, OR
//  (b) the movie does not require rent-or-buy AND the trial has not expired.
permit (
    principal is TrialMember,
    action == Action::"watch",
    resource is Movie
)
when {
    resource.isFree
    || (!resource.needsRentOrBuy && context.now.datetime < principal.trialExpiry)
};
