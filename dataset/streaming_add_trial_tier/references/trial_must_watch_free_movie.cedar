// Floor: a TrialMember MUST be permitted to watch any free Movie
// (regardless of trial expiry status — free is always free).
permit (
    principal is TrialMember,
    action == Action::"watch",
    resource is Movie
)
when {
    resource.isFree
};
