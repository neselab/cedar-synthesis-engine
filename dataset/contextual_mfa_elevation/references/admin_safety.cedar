// Ceiling: adminOperation permitted only when same workspace AND admin
// role AND MFA is fresh.
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
