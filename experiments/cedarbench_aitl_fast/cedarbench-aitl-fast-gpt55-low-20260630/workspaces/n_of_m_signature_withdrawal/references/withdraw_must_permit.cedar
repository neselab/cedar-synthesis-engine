// Floor: any of the five eligible signers MUST be able to withdraw a
// signature (the host app enforces "you can only withdraw your own"
// downstream).
permit (
    principal is Signer,
    action == Action::"withdrawSignature",
    resource is Proposal
)
when {
    principal == Signer::"s1"
    || principal == Signer::"s2"
    || principal == Signer::"s3"
    || principal == Signer::"s4"
    || principal == Signer::"s5"
};
