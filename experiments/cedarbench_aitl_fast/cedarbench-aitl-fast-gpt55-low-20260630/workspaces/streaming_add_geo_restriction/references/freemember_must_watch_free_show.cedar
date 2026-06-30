// Floor: FreeMember MUST watch any free Show when the request region is in
// the show's allowedRegions.
permit (
    principal is FreeMember,
    action == Action::"watch",
    resource is Show
)
when {
    resource.isFree && resource.allowedRegions.contains(context.region)
};
