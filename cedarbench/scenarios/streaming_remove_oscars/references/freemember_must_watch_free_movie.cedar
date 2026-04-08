// Floor: FreeMember MUST be permitted to watch any free Movie.
// FreeMember has no profile attribute, so the bedtime forbid does not apply
// to it (the schema would type-error if a forbid tried `principal.profile`
// without an `is Subscriber` guard).
permit (
    principal is FreeMember,
    action == Action::"watch",
    resource is Movie
)
when {
    resource.isFree
};
