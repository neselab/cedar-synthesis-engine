// Floor (level 2 — first re-permit): under platform lockout, a user
// holding hasEmergencyAuth must still be permitted to `access` while
// emergencyMode is true. Respects §8.8: red-cell still wins unless the
// user also has hasOverride.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    context.emergencyMode
    && principal.hasEmergencyAuth
    && !(context.redCellLockdown && !principal.hasOverride)
};
