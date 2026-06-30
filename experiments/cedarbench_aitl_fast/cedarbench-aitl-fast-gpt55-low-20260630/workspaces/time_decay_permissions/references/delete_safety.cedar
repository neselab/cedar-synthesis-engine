// Ceiling: delete is permitted only when context.now >= principal.lastAuthAt
// AND either
//   (a) age < 1h  (fresh -- any sensitivity), OR
//   (b) age < 4h AND resource.sensitivity == 1  (stale -- low sensitivity only).
// Same shape as write_safety: delete is treated as a write-class action
// for the purposes of the credential-aging policy.
permit (
    principal is Operator,
    action == Action::"delete",
    resource is Resource
)
when {
    context.now >= principal.lastAuthAt
    && (
        context.now.durationSince(principal.lastAuthAt) < duration("1h")
        || (
            context.now.durationSince(principal.lastAuthAt) < duration("4h")
            && resource.sensitivity == 1
        )
    )
};
