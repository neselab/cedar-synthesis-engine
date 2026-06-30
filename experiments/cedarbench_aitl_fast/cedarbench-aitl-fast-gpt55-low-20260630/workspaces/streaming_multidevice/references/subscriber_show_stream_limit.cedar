// Ceiling: Subscriber may watch a Show only when their tier's stream limit
// is respected: standard < 2, premium < 5.
permit (
    principal is Subscriber,
    action == Action::"watch",
    resource is Show
)
when {
    (principal.subscription.tier != "standard" || context.activeStreams < 2)
    && (principal.subscription.tier != "premium" || context.activeStreams < 5)
};
