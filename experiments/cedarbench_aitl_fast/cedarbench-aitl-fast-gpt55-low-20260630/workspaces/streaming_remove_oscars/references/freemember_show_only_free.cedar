// Ceiling: FreeMember may watch a Show only when isFree.
permit (
    principal is FreeMember,
    action == Action::"watch",
    resource is Show
)
when {
    resource.isFree
};
