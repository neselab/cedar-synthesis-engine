// Floor: any non-suspended MFA-verified user MUST be able to `view` a
// classified resource regardless of business hours or approval status.
// Both forbid 1 (suspension) and forbid 3 (classified-MFA) are negated.
permit (
    principal is User,
    action == Action::"view",
    resource is Resource
)
when {
    !principal.isSuspended
    && resource.isClassified
    && principal.mfaVerified
};
