// Ceiling: FreeMember may watch a Show only when activeStreams < 1.
permit (
    principal is FreeMember,
    action == Action::"watch",
    resource is Show
)
when {
    context.activeStreams < 1
};
