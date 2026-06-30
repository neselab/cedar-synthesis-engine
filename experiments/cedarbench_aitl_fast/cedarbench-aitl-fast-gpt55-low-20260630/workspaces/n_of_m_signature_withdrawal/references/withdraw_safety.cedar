// Ceiling for withdrawSignature: only the five eligible signers may
// withdraw. The host application enforces "you can only withdraw your
// own signature" downstream.
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
