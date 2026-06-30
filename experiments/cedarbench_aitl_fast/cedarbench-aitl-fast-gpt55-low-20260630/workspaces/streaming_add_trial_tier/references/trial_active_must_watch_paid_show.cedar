// Floor: a TrialMember whose trial is still active MUST be permitted to
// watch any non-early-access Show.
permit (
    principal is TrialMember,
    action == Action::"watch",
    resource is Show
)
when {
    !resource.isEarlyAccess && context.now.datetime < principal.trialExpiry
};
