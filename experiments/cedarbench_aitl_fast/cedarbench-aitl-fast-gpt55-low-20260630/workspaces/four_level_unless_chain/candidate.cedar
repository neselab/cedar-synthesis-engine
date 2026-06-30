permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    !context.lockoutActive
    || (context.emergencyMode && principal.hasEmergencyAuth)
    || (context.commanderOverrideActive && principal.role == "commander")
}
unless {
    context.redCellLockdown && !principal.hasOverride
};

permit (
    principal is User,
    action == Action::"forceAccess",
    resource is Resource
)
when {
    principal.role == "commander" && principal.hasOverride
};