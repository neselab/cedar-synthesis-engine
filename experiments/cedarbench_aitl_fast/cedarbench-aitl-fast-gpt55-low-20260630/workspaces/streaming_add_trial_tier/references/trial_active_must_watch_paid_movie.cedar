// Floor: a TrialMember whose trial is still active MUST be permitted to
// watch any non-rent-or-buy Movie. The bedtime forbid does not apply to
// TrialMember (no `profile` attribute), so no §8.8 exclusion is needed.
permit (
    principal is TrialMember,
    action == Action::"watch",
    resource is Movie
)
when {
    !resource.needsRentOrBuy && context.now.datetime < principal.trialExpiry
};
