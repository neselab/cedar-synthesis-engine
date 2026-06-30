// Ceiling: a Subscriber may watch a Show only when either (a) the show is
// not in its early-access window, or (b) the subscriber is on the premium
// tier. Standard-tier subscribers cannot watch early-access shows.
permit (
    principal is Subscriber,
    action == Action::"watch",
    resource is Show
)
when {
    !resource.isEarlyAccess || principal.subscription.tier == "premium"
};
