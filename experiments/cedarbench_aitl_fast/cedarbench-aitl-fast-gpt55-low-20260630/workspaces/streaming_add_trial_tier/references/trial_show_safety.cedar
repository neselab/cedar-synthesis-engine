// Ceiling: a TrialMember may watch a Show only when at least one of:
//  (a) the show is free, OR
//  (b) the show is not in early access AND the trial has not expired.
permit (
    principal is TrialMember,
    action == Action::"watch",
    resource is Show
)
when {
    resource.isFree
    || (!resource.isEarlyAccess && context.now.datetime < principal.trialExpiry)
};
