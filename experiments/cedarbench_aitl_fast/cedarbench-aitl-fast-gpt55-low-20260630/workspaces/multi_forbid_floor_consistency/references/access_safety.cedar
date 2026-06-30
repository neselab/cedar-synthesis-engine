// Ceiling for `access`: permit only when NONE of the four forbid
// conditions are triggered. Encoded as a conjunction of negations of
// each forbid condition.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    !principal.isSuspended
    && !context.outsideBusinessHours
    && (!resource.isClassified || principal.mfaVerified)
    && (!resource.requiresApproval || context.approvalGranted)
};
