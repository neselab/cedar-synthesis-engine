// Ceiling: Subscriber may watch a Movie only when in the movie's allowedRegions.
permit (
    principal is Subscriber,
    action == Action::"watch",
    resource is Movie
)
when {
    resource.allowedRegions.contains(context.region)
};
