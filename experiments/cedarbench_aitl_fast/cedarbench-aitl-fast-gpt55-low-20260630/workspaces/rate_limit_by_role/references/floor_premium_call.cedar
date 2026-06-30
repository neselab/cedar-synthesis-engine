// Floor: a premium-tier client MUST be able to call any endpoint
// with no rate limit.
// No global forbids to exclude.
permit (
    principal is ApiClient,
    action == Action::"call",
    resource is Endpoint
)
when {
    principal.tier == "premium"
};
