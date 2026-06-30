// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
    principal is Operator,
    action == Action::"read",
    resource is Resource
)
when {
    context.now >= principal.lastAuthAt &&
    context.now.durationSince(principal.lastAuthAt) < duration("4h")
};

permit (
    principal is Operator,
    action == Action::"write",
    resource is Resource
)
when {
    context.now >= principal.lastAuthAt &&
    context.now.durationSince(principal.lastAuthAt) < duration("4h") &&
    (
        context.now.durationSince(principal.lastAuthAt) < duration("1h") ||
        resource.sensitivity == 1
    )
};

permit (
    principal is Operator,
    action == Action::"delete",
    resource is Resource
)
when {
    context.now >= principal.lastAuthAt &&
    context.now.durationSince(principal.lastAuthAt) < duration("4h") &&
    (
        context.now.durationSince(principal.lastAuthAt) < duration("1h") ||
        resource.sensitivity == 1
    )
};
