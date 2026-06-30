// Floor: any non-suspended MFA-verified user MUST be able to `access` a
// classified, approval-flagged resource during business hours when the
// approval is attested. Maximum-stress floor: all four forbid negations
// must be present and consistent.
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
    && resource.requiresApproval
    && context.approvalGranted
};
