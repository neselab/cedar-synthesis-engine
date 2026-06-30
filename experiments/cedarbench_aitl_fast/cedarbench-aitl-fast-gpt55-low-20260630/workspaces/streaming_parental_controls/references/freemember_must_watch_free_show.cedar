// Floor: FreeMember MUST watch any free Show.
permit (
    principal is FreeMember,
    action == Action::"watch",
    resource is Show
)
when {
    resource.isFree
};
