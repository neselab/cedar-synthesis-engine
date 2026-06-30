// Floor: a concrete probe where the SELF expiry is the binding
// (earlier) one. selfExpiresAt = 2025-06-01T11:00:00Z is earlier
// than parentExpiresAt = 2025-06-01T18:00:00Z, so the effective
// expiry is self's. now = 2025-06-01T10:30:00Z is strictly before
// both, so the request MUST be permitted.
permit (
    principal is User,
    action == Action::"useSession",
    resource is Resource
)
when {
    context.now == datetime("2025-06-01T10:30:00Z")
    && context.session.parentExpiresAt == datetime("2025-06-01T18:00:00Z")
    && context.session.selfExpiresAt == datetime("2025-06-01T11:00:00Z")
};
