// Floor: a whitelisted, non-blacklisted caller with a trusted-source request
// MUST be permitted to invoke. This is the full positive conjunction —
// the candidate must permit the entire positive region.
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
