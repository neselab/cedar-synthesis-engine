// Floor: User with fresh MFA (verified within the last 15 minutes)
// MUST be permitted to deleteDocument on a Document in their own workspace.
permit (
    principal is User,
    action == Action::"deleteDocument",
    resource is Document
)
when {
    principal.workspace == resource.workspace
    && context.now.datetime.durationSince(principal.mfaVerifiedAt) < duration("15m")
};
