// Ceiling: a FreeMember may watch a Show only when the show is free.
permit (
    principal is FreeMember,
    action == Action::"watch",
    resource is Show
)
when {
    resource.isFree
};
