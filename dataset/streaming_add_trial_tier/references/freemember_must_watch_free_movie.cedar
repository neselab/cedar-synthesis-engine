// Floor: any FreeMember MUST be permitted to watch any Movie that is free.
// Free members have no other watch grants, so this floor is the only
// requirement on FreeMember + watch + Movie. The bedtime forbid does not
// apply to FreeMember principals (they have no `profile` attribute), so no
// global-forbid exclusion is needed in the floor's when clause.
permit (
    principal is FreeMember,
    action == Action::"watch",
    resource is Movie
)
when {
    resource.isFree
};
