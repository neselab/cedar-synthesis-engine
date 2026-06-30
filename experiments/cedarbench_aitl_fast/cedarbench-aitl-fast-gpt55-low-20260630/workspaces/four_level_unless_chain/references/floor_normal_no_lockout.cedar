// Floor (level 1 — base case): with no platform lockout and no red-cell
// lockdown, any user must be permitted to `access` the resource.
// Respects §8.8: explicitly excludes the red-cell unless condition.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    !context.lockoutActive
    && !(context.redCellLockdown && !principal.hasOverride)
};
