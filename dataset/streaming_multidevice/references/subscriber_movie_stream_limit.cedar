// Ceiling: Subscriber may watch a Movie only when their tier's stream limit
// is respected:
//  - tier == "standard" → activeStreams < 2
//  - tier == "premium"  → activeStreams < 5
// Encoded as the conjunction of two implications. Subscribers with any
// other tier value have no stream limit per the spec.
permit (
    principal is Subscriber,
    action == Action::"watch",
    resource is Movie
)
when {
    (principal.subscription.tier != "standard" || context.activeStreams < 2)
    && (principal.subscription.tier != "premium" || context.activeStreams < 5)
};
