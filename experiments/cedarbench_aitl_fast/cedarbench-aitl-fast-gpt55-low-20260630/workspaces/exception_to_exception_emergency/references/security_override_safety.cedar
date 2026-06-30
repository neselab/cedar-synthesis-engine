// Ceiling for action `securityOverride`. Only securityClearance holders
// may invoke this action; lockout/break-glass/lockdown context is
// irrelevant to the permission shape (it remains administrator-only).
permit (
    principal is User,
    action == Action::"securityOverride",
    resource is Resource
)
when {
    principal.securityClearance
};
