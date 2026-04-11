// Floor: Subscriber MUST be permitted to download any non-free Movie.
// The download action is not subject to the bedtime forbid (which only
// applies to `watch`), so no §8.8 floor-bound consistency exclusion is
// needed for this floor.
permit (
    principal is Subscriber,
    action == Action::"download",
    resource is Movie
)
when {
    !resource.isFree
};
