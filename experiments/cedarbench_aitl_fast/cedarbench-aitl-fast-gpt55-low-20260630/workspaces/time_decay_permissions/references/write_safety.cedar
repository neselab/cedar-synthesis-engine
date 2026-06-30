// Ceiling: write is permitted only when context.now >= principal.lastAuthAt
// AND either
//   (a) age < 1h  (fresh -- any sensitivity), OR
//   (b) age < 4h AND resource.sensitivity == 1  (stale -- low sensitivity only).
// Equivalently: never when expired (age >= 4h), and never when stale +
// sensitivity > 1.
permit (
    principal is Operator,
    action == Action::"write",
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
