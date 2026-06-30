// Ceiling: FreeMember may watch a Movie only when the request region is in
// the movie's allowedRegions set.
permit (
    principal is FreeMember,
    action == Action::"watch",
    resource is Movie
)
when {
    resource.allowedRegions.contains(context.region)
};
