// Floor: admin User with fresh MFA MUST be permitted to perform
// adminOperation on their own workspace.
permit (
    principal is User,
    action == Action::"adminOperation",
    resource is Workspace
)
when {
    principal.workspace == resource
    && principal.isAdmin
    && context.now.datetime.durationSince(principal.mfaVerifiedAt) < duration("15m")
};
