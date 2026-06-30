// Floor: a clearance holder MUST be permitted to access during a
// security lockdown when the request would otherwise be in the normal
// path (no lockout). This exercises the Tier-3 carve-out: even with
// securityLockdownActive == true, securityClearance == true users still
// pass.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    !context.lockoutActive
    && context.securityLockdownActive
    && principal.securityClearance
};
