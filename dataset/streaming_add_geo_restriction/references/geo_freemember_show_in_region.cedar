// Ceiling: FreeMember may watch a Show only when the request region is in
// the show's allowedRegions set.
permit (
    principal is FreeMember,
    action == Action::"watch",
    resource is Show
)
when {
    resource.allowedRegions.contains(context.region)
};
