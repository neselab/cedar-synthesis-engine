// Floor: any non-suspended MFA-verified user MUST be able to `access` a
// classified, non-approval-flagged resource during business hours.
// Includes all four forbid negations.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    !principal.isSuspended
    && !context.outsideBusinessHours
    && resource.isClassified
    && principal.mfaVerified
    && !resource.requiresApproval
};
