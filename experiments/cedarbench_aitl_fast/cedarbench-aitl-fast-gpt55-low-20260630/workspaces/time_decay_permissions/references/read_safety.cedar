// Ceiling: read is permitted only when context.now >= principal.lastAuthAt
// AND the credential age is < 4h (i.e. fresh OR stale, but not expired).
// Sensitivity is irrelevant for read.
permit (
    principal is Operator,
    action == Action::"read",
    resource is Resource
)
when {
    context.now >= principal.lastAuthAt
    && context.now.durationSince(principal.lastAuthAt) < duration("4h")
};
