// Ceiling: FreeMember may watch a Movie only when isFree.
permit (
    principal is FreeMember,
    action == Action::"watch",
    resource is Movie
)
when {
    resource.isFree
};
