// Floor: a commander holding hasOverride must be permitted to
// forceAccess regardless of any context flags (lockoutActive,
// emergencyMode, commanderOverrideActive, redCellLockdown).
permit (
    principal is User,
    action == Action::"forceAccess",
    resource is Resource
)
when {
    principal.role == "commander" && principal.hasOverride
};
