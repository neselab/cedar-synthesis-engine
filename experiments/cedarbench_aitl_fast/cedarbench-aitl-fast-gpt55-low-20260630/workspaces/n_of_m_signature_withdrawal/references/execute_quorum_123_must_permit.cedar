// Floor: when activeSigners contains {s1, s2, s3} (the canonical
// "first" 3-of-5 subset), the candidate MUST permit any of the five
// eligible signers to executeProposal.
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
    && context.activeSigners.containsAll([Signer::"s1", Signer::"s2", Signer::"s3"])
};
