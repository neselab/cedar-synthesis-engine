// Floor: FreeMember MUST be permitted to watch any free Movie.
permit (
    principal is FreeMember,
    action == Action::"watch",
    resource is Movie
)
when {
    resource.isFree
};
