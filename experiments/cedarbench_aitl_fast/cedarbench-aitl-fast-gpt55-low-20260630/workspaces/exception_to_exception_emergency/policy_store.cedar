// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    !context.lockoutActive
    || (
        context.lockoutActive
        && context.breakGlassInvoked
        && principal.hasBreakGlass
    )
}
unless {
    context.securityLockdownActive && !principal.securityClearance
};

permit (
    principal is User,
    action == Action::"securityOverride",
    resource is Resource
)
when {
    principal.securityClearance
};
