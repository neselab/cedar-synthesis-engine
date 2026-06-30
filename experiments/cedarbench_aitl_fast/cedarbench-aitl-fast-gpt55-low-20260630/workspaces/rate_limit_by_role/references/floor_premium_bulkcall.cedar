// Floor: a premium-tier client MUST be able to bulkCall when under
// the bulk rate limit.
// No global forbids to exclude.
permit (
    principal is ApiClient,
    action == Action::"bulkCall",
    resource is Endpoint
)
when {
    principal.tier == "premium"
    && context.requestsThisMinute < 500
};
