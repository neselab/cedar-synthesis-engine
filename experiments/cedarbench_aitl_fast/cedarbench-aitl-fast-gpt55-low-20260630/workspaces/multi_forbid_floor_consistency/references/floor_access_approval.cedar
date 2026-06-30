// Floor: any non-suspended user MUST be able to `access` a
// non-classified, approval-flagged resource during business hours when
// the approval is attested. Includes all four forbid negations.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    !principal.isSuspended
    && !context.outsideBusinessHours
    && !resource.isClassified
    && resource.requiresApproval
    && context.approvalGranted
};
