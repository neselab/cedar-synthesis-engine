// Floor: in normal mode (no lockout), any user MUST be permitted to
// access any Resource — UNLESS the global Tier-3 trump applies (security
// lockdown denies everyone without clearance).
//
// §8.8 floor-bound consistency: the !securityLockdownActive ||
// principal.securityClearance guard is required because the spec's
// global `unless` clause denies any request matching the negation.
permit (
    principal is User,
    action == Action::"access",
    resource is Resource
)
when {
    !context.lockoutActive
    && (!context.securityLockdownActive || principal.securityClearance)
};
