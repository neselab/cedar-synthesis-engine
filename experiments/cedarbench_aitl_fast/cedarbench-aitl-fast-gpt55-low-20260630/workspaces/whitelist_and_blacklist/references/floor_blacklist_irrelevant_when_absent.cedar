// Floor: when the caller is whitelisted, NOT in the blacklist, and trusted,
// the request must be permitted EVEN if the blacklist is non-empty (i.e.
// the blacklist must not block callers who are absent from it). This
// floor documents that the denylist check is per-principal membership,
// not a blanket "any blacklist entries" gate.
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
