// Floor: during a lockout, a user with hasBreakGlass who has invoked
// break-glass MUST be permitted to access — UNLESS the Tier-3 trump
// applies. §8.8 guard included.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    context.lockoutActive
    && context.breakGlassInvoked
    && principal.hasBreakGlass
    && (!context.securityLockdownActive || principal.securityClearance)
};
