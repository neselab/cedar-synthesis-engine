// Floor: FreeMember MUST watch any free Movie when in region. Geo is the
// only forbid that applies to FreeMember (no profile → bedtime and age
// rating forbids cannot fire).
permit (
    principal is FreeMember,
    action == Action::"watch",
    resource is Movie
)
when {
    resource.isFree && resource.allowedRegions.contains(context.region)
};
