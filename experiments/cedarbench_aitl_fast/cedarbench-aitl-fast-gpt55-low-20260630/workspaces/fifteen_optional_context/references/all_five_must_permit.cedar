// Floor: when ALL FIVE required attestations are present and true,
// access MUST be permitted (and remains permitted regardless of which
// of the other ten optional attributes are present or absent).
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
