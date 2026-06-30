// Ceiling: viewByTag is permitted ONLY when:
//   1. resource.tags is non-empty (safe default for empty set), and
//   2. context.requestedTag is a non-empty string (safe default for
//      empty filter), and
//   3. resource.tags contains context.requestedTag.
//
// The first two guards are not in the literal spec sentence; they are
// the planner's safe-default inference for edge cases the spec is
// silent about. Without them, an upstream bug that inserts "" into a
// document's tag set, combined with a client-supplied "" filter, would
// permit unintended access.
permit (
    principal is User,
    action == Action::"viewByTag",
    resource is Document
)
when {
    !resource.tags.isEmpty()
    && context.requestedTag != ""
    && resource.tags.contains(context.requestedTag)
};
