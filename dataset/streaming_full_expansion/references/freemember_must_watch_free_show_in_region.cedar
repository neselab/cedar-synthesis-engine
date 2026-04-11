// Floor: FreeMember MUST watch any free Show when in region.
permit (
    principal is FreeMember,
    action == Action::"watch",
    resource is Show
)
when {
    resource.isFree && resource.allowedRegions.contains(context.region)
};
