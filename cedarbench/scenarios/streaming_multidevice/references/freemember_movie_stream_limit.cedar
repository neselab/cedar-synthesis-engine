// Ceiling: FreeMember may watch a Movie only when activeStreams < 1
// (i.e., no other concurrent stream is active on the account).
permit (
    principal is FreeMember,
    action == Action::"watch",
    resource is Movie
)
when {
    context.activeStreams < 1
};
