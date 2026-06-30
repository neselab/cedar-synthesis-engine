// Floor: a concrete probe in the STALE window (2 hours since
// lastAuthAt) reading a HIGH-sensitivity (== 3) resource. Stale-window
// access still permits read for any sensitivity, so this MUST be
// permitted.
permit (
    principal is Operator,
    action == Action::"read",
    resource is Resource
)
when {
    context.now == datetime("2025-06-01T14:00:00Z")
    && principal.lastAuthAt == datetime("2025-06-01T12:00:00Z")
    && resource.sensitivity == 3
};
