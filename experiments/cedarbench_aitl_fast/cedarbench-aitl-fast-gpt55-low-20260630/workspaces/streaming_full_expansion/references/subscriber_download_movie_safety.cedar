// Ceiling: Subscriber may download a Movie only when the movie is NOT free.
// (Free content is streaming-only and cannot be downloaded.)
permit (
    principal is Subscriber,
    action == Action::"download",
    resource is Movie
)
when {
    !resource.isFree
};
