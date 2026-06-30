// Ceiling for action `access`. Encodes the maximal permissive shape:
//   - normal path: !lockoutActive
//   - break-glass path: lockoutActive && breakGlassInvoked && hasBreakGlass
// AND the global Tier-3 trump:
//   - if securityLockdownActive, only securityClearance holders pass.
//
// Any candidate must be no-more-permissive than this.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    !context.lockoutActive
    || (context.lockoutActive
        && context.breakGlassInvoked
        && principal.hasBreakGlass)
}
unless {
    context.securityLockdownActive && !principal.securityClearance
};
