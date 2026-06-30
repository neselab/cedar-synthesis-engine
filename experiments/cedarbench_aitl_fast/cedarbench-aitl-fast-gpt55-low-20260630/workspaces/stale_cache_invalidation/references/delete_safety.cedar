// Ceiling: delete permitted only when role is "admin" AND mfaTimestamp
// is present AND MFA was completed within the last 30 seconds.
permit (
    principal is User,
    action == Action::"delete",
    resource is Resource
)
when {
    principal.role == "admin"
    && context has mfaTimestamp
    && context.now.durationSince(context.mfaTimestamp) < duration("30s")
};
