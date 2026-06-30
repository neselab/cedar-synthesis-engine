// Ceiling for viewProposal: only the five eligible signers may view.
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
