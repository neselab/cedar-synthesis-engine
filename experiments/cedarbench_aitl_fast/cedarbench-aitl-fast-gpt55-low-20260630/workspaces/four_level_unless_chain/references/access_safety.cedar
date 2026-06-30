// Ceiling: access permitted only when the four-level unless chain
// resolves to "permit". The permit-side disjunction covers (a) base
// no-lockout, (b) emergency mode + hasEmergencyAuth, (c) commander
// override window + commander role. The trailing exclusion encodes
// the red-cell hard lockout, which only the hasOverride token bypasses.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    (
        !context.lockoutActive
        || (context.emergencyMode && principal.hasEmergencyAuth)
        || (context.commanderOverrideActive && principal.role == "commander")
    )
    && !(context.redCellLockdown && !principal.hasOverride)
};
