// Floor: FreeMember MUST watch any free Show when activeStreams < 1.
permit (
    principal is FreeMember,
    action == Action::"watch",
    resource is Show
)
when {
    resource.isFree && context.activeStreams < 1
};
