// Floor: when caller is whitelisted, not blacklisted, and the request is
// flagged trustedSource, the candidate MUST permit. This floor documents
// the contrapositive of the trusted-source gate: a permitted caller with
// the trusted flag set is not over-restricted by candidate policies.
permit (
    principal is Caller,
    action == Action::"invoke",
    resource is Endpoint
)
when {
    resource.whitelistedCallers.contains(principal)
    && !resource.blacklistedCallers.contains(principal)
    && context.trustedSource == true
};
