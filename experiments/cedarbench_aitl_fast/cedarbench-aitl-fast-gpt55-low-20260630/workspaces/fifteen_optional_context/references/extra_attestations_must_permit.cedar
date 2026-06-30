// Floor: even when one of the non-required attestations
// (`complianceFlag`) is present and FALSE, access MUST still be
// permitted as long as the five required attestations are present
// and true. This pins the policy to NOT accidentally require any of
// the other ten optional attributes.
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
    && context has complianceFlag
    && context.mfaToken
    && context.deviceTrusted
    && context.locationVerified
    && context.identityProofed
    && context.auditLoggingEnabled
    && !context.complianceFlag
};
