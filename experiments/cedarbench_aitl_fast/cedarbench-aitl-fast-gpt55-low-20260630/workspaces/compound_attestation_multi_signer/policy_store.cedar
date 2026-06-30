// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
    principal is User,
    action == Action::"view",
    resource is Proposal
);

permit (
    principal is User,
    action == Action::"execute",
    resource is Proposal
)
when {
    context has attestation1 &&
    context has attestation2 &&
    context has attestation3 &&

    context.attestation1.signer in resource.requiredSigners &&
    context.attestation2.signer in resource.requiredSigners &&
    context.attestation3.signer in resource.requiredSigners &&

    context.attestation1.signer != context.attestation2.signer &&
    context.attestation1.signer != context.attestation3.signer &&
    context.attestation2.signer != context.attestation3.signer &&

    context.now <= context.attestation1.validUntil &&
    context.now <= context.attestation2.validUntil &&
    context.now <= context.attestation3.validUntil
};
