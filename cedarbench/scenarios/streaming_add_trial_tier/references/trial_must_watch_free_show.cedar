// Floor: a TrialMember MUST be permitted to watch any free Show.
permit (
    principal is TrialMember,
    action == Action::"watch",
    resource is Show
)
when {
    resource.isFree
};
