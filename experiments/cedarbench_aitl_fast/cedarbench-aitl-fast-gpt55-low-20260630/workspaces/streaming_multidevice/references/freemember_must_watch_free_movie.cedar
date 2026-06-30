// Floor: FreeMember MUST watch any free Movie when activeStreams < 1.
// `activeStreams < 1` is the §8.8 floor-bound consistency exclusion for the
// FreeMember concurrent-stream forbid (which fires when activeStreams >= 1).
permit (
    principal is FreeMember,
    action == Action::"watch",
    resource is Movie
)
when {
    resource.isFree && context.activeStreams < 1
};
