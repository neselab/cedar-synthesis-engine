// Floor: any non-suspended user MUST be able to `view` a non-classified
// resource regardless of business hours or approval status (forbids 2
// and 4 do not apply to `view`). Only forbid 1 (suspension) needs to
// be negated; forbid 3 (classified-MFA) is satisfied by !isClassified.
permit (
    principal is User,
    action == Action::"view",
    resource is Resource
)
when {
    !principal.isSuspended
    && !resource.isClassified
};
