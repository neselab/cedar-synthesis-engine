// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
    principal is User,
    action == Action::"performAction",
    resource is Resource
)
when {
    context.now >= principal.lastActionAt
    && context.now.durationSince(principal.lastActionAt) > duration("1h")
};
