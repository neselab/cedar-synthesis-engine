// Floor: any of the five eligible signers MUST be able to add a
// signature.
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
