// Floor: a securityClearance holder MUST be permitted to invoke
// securityOverride. The action is administrator-only and unaffected
// by lockout/break-glass/lockdown context.
permit (
    principal is User,
    action == Action::"securityOverride",
    resource is Resource
)
when {
    principal.securityClearance
};
