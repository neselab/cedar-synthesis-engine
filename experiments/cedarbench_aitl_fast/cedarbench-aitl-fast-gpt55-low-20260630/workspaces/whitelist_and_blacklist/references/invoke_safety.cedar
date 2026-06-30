// Ceiling: invoke permitted only when caller is whitelisted, NOT blacklisted,
// AND request has trustedSource flag set.
permit (
    principal is Caller,
    action == Action::"invoke",
    resource is Endpoint
)
when {
    resource.whitelistedCallers.contains(principal)
    && !resource.blacklistedCallers.contains(principal)
    && context.trustedSource
};
