// Ceiling: execute permitted ONLY when all three attestation records
// are present, each signer is in resource.requiredSigners, the three
// signers are pairwise distinct, and each attestation is currently
// valid (now <= validUntil). Nine-clause conjunction: drop any clause
// and the candidate becomes too permissive.
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
