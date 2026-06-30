// Ceiling: view permitted ONLY when the principal is the recorded
// owner AND, if a claimedOwner is asserted in the context, that
// assertion agrees with the recorded owner. Divergent claims are
// treated as tampering / staleness signals and denied.
//
// The has-guard form below avoids the negated-`has` trap (§8.3):
// Cedar's type-checker does not propagate negation through `has`,
// so we must repeat `context has claimedOwner` inside the
// equality-disjunct branch.
permit (
    principal is User,
    action == Action::"view",
    resource is Document
)
when {
    principal == resource.recordedOwner
    && (
        !(context has claimedOwner)
        || (context has claimedOwner && context.claimedOwner == resource.recordedOwner)
    )
};
