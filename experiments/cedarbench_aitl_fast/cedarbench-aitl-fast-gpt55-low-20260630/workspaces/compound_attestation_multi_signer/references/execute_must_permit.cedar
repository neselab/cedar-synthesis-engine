// Floor: execute MUST be permitted when all three attestation records
// are present, each signer is in resource.requiredSigners, all three
// signers are distinct, and all three attestations are valid. This is
// the same nine-clause conjunction as the ceiling — the candidate
// must permit at least every request the ceiling permits.
permit (
    principal is User,
    action == Action::"execute",
    resource is Proposal
)
when {
    context has attestation1
    && context has attestation2
    && context has attestation3
    && resource.requiredSigners.contains(context.attestation1.signer)
    && resource.requiredSigners.contains(context.attestation2.signer)
    && resource.requiredSigners.contains(context.attestation3.signer)
    && context.attestation1.signer != context.attestation2.signer
    && context.attestation1.signer != context.attestation3.signer
    && context.attestation2.signer != context.attestation3.signer
    && context.now <= context.attestation1.validUntil
    && context.now <= context.attestation2.validUntil
    && context.now <= context.attestation3.validUntil
};
