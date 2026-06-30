// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
permit (
    principal is Caller,
    action == Action::"invoke",
    resource is Endpoint
)
when {
    resource.whitelistedCallers.contains(principal) &&
    !resource.blacklistedCallers.contains(principal) &&
    context.trustedSource == true
};
