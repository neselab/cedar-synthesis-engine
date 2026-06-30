// Floor: a concrete probe in the STALE window (2 hours since
// lastAuthAt) writing a LOW-sensitivity (== 1) resource. Stale-window
// write is permitted ONLY for sensitivity == 1, so this MUST be
// permitted.
permit (
    principal is Operator,
    action == Action::"write",
    resource is Resource
)
when {
    context.now == datetime("2025-06-01T14:00:00Z")
    && principal.lastAuthAt == datetime("2025-06-01T12:00:00Z")
    && resource.sensitivity == 1
};
