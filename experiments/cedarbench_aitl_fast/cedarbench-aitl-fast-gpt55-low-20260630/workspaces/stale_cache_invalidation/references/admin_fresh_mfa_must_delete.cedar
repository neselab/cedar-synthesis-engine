// Floor: an admin User with a fresh (< 30s) mfaTimestamp MUST be
// permitted to delete.
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
