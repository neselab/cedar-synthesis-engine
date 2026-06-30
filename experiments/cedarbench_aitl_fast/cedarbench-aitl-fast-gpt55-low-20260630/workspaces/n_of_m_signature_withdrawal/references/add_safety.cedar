// Ceiling for addSignature: only the five eligible signers may add a
// signature. The off-Cedar signing service is responsible for tracking
// the actual signed set; Cedar only gates whether the principal is
// allowed to interact with the proposal.
permit (
    principal is Signer,
    action == Action::"addSignature",
    resource is Proposal
)
when {
    principal == Signer::"s1"
    || principal == Signer::"s2"
    || principal == Signer::"s3"
    || principal == Signer::"s4"
    || principal == Signer::"s5"
};
