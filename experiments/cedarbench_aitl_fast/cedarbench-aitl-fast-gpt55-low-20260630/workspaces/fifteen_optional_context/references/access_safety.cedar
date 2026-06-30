// Ceiling: accessFederatedResource permitted ONLY when all five of
// the required attestations are PRESENT and TRUE. Each optional
// attribute is paired with its own `has` guard before the read
// (§8.3 has-guard discipline). Drop any clause and the candidate
// becomes too permissive.
permit (
    principal is User,
    action == Action::"accessFederatedResource",
    resource is Resource
)
when {
    context has mfaToken
    && context has deviceTrusted
    && context has locationVerified
    && context has identityProofed
    && context has auditLoggingEnabled
    && context.mfaToken
    && context.deviceTrusted
    && context.locationVerified
    && context.identityProofed
    && context.auditLoggingEnabled
};
