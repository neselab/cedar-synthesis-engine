// Floor: when activeSigners contains {s3, s4, s5} (the "last" 3-of-5
// subset — a common omission target if the candidate enumerates the
// disjuncts incompletely), the candidate MUST permit executeProposal.
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
    && context.activeSigners.containsAll([Signer::"s3", Signer::"s4", Signer::"s5"])
};
