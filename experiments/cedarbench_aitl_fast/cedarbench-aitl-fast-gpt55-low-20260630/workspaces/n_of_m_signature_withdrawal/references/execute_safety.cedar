// Ceiling for executeProposal: the candidate may permit ONLY when the
// principal is one of the five eligible signers AND context.activeSigners
// is a superset of at least one 3-element subset of {s1, s2, s3, s4, s5}.
//
// Cedar has no .size() operator, so the threshold is encoded as a
// disjunction over the C(5,3) = 10 possible 3-of-5 subsets, each tested
// with .containsAll().
permit (
    principal is Signer,
    action == Action::"executeProposal",
    resource is Proposal
)
when {
    (principal == Signer::"s1"
     || principal == Signer::"s2"
     || principal == Signer::"s3"
     || principal == Signer::"s4"
     || principal == Signer::"s5")
    && (
        context.activeSigners.containsAll([Signer::"s1", Signer::"s2", Signer::"s3"])
     || context.activeSigners.containsAll([Signer::"s1", Signer::"s2", Signer::"s4"])
     || context.activeSigners.containsAll([Signer::"s1", Signer::"s2", Signer::"s5"])
     || context.activeSigners.containsAll([Signer::"s1", Signer::"s3", Signer::"s4"])
     || context.activeSigners.containsAll([Signer::"s1", Signer::"s3", Signer::"s5"])
     || context.activeSigners.containsAll([Signer::"s1", Signer::"s4", Signer::"s5"])
     || context.activeSigners.containsAll([Signer::"s2", Signer::"s3", Signer::"s4"])
     || context.activeSigners.containsAll([Signer::"s2", Signer::"s3", Signer::"s5"])
     || context.activeSigners.containsAll([Signer::"s2", Signer::"s4", Signer::"s5"])
     || context.activeSigners.containsAll([Signer::"s3", Signer::"s4", Signer::"s5"])
    )
};
