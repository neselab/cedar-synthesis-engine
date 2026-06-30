// Floor: any Subscriber MUST be permitted to watch any Show that is past
// its early-access window, AS LONG AS the kid profile is not enabled.
// The `!principal.profile.isKid` clause excludes the kid-bedtime forbid
// from interfering (per §8.8 floor-bound consistency rule).
permit (
    principal is Subscriber,
    action == Action::"watch",
    resource is Show
)
when {
    !resource.isEarlyAccess && !principal.profile.isKid
};
