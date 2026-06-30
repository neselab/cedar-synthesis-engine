// Floor: FreeMember MUST watch any free Movie when the request region is in
// the movie's allowedRegions. The geo exclusion is the §8.8 floor-bound
// consistency exclusion for the global geo forbid (which applies to ALL
// principals including FreeMember).
permit (
    principal is FreeMember,
    action == Action::"watch",
    resource is Movie
)
when {
    resource.isFree && resource.allowedRegions.contains(context.region)
};
