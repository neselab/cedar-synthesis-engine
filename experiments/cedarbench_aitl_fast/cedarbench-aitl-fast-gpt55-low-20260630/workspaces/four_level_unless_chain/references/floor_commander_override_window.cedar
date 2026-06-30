// Floor (level 3 — second re-permit): when commanderOverrideActive is
// true, a commander must be permitted to `access`, regardless of
// lockoutActive or emergencyMode. Respects §8.8: red-cell still wins
// unless the commander also holds hasOverride.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    context.commanderOverrideActive
    && principal.role == "commander"
    && !(context.redCellLockdown && !principal.hasOverride)
};
