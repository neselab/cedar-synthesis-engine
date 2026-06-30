// Floor: any of the five eligible signers MUST be able to view a
// proposal (no quorum requirement).
permit (
    principal is Signer,
    action == Action::"viewProposal",
    resource is Proposal
)
when {
    principal == Signer::"s1"
    || principal == Signer::"s2"
    || principal == Signer::"s3"
    || principal == Signer::"s4"
    || principal == Signer::"s5"
};
