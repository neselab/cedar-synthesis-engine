// Floor (level 4 — final bypass): even under redCellLockdown, a user
// holding hasOverride must be permitted to `access` provided some
// permit-side condition holds (here: no platform lockout). Tests that
// the candidate honors hasOverride as the unique escape from the
// red-cell hard exclusion.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    !context.lockoutActive
    && principal.hasOverride
};
