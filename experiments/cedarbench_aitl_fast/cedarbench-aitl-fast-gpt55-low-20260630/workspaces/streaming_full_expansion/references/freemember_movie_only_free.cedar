// Ceiling: a FreeMember may watch a Movie only when the movie is free.
permit (
    principal is FreeMember,
    action == Action::"watch",
    resource is Movie
)
when {
    resource.isFree
};
