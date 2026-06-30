// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
    principal is User,
    action == Action::"invoke",
    resource is CriticalEndpoint
)
when {
    context has nonce && resource.validNonces.contains(context.nonce)
};
