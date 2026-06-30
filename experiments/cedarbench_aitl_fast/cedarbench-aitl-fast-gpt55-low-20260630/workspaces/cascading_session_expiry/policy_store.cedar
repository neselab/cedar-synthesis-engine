// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
    principal is User,
    action == Action::"useSession",
    resource is Resource
) when {
    context.now < context.session.parentExpiresAt &&
    context.now < context.session.selfExpiresAt
};
