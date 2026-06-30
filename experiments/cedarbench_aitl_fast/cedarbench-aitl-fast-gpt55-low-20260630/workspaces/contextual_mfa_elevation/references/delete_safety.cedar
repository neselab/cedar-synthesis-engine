// Ceiling: deleteDocument permitted only when same workspace AND MFA
// is fresh (verified within the last 15 minutes).
permit (
    principal is User,
    action == Action::"deleteDocument",
    resource is Document
)
when {
    principal.workspace == resource.workspace
    && context.now.datetime.durationSince(principal.mfaVerifiedAt) < duration("15m")
};
