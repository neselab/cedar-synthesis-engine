// Floor: any non-suspended user MUST be able to `access` a clean
// resource (not classified, not approval-flagged) during business
// hours. Includes ALL FOUR forbid negations to be consistent with the
// global forbids per §8.8.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    !principal.isSuspended
    && !context.outsideBusinessHours
    && !resource.isClassified
    && !resource.requiresApproval
};
