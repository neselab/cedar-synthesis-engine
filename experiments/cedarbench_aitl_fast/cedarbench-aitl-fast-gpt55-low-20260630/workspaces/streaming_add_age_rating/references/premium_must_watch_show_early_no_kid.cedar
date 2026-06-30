// Floor: a Subscriber on the premium tier MUST be permitted to watch a
// Show during its early-access window, AS LONG AS the kid profile is not
// enabled. This is the only path to watching early-access content; the
// kid-bedtime forbid is excluded by `!principal.profile.isKid` per §8.8.
permit (
    principal is Subscriber,
    action == Action::"watch",
    resource is Show
)
when {
    resource.isEarlyAccess
    && principal.subscription.tier == "premium"
    && !principal.profile.isKid
};
