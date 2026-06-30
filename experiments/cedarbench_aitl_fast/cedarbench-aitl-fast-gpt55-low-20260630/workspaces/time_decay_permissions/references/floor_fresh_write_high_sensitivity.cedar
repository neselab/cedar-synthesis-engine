// Floor: a concrete probe in the FRESH window (30 minutes since
// lastAuthAt) writing a HIGH-sensitivity (== 3) resource. Fresh-window
// access permits all actions for any sensitivity, so this MUST be
// permitted.
permit (
    principal is Operator,
    action == Action::"write",
    resource is Resource
)
when {
    context.now == datetime("2025-06-01T12:30:00Z")
    && principal.lastAuthAt == datetime("2025-06-01T12:00:00Z")
    && resource.sensitivity == 3
};
