// Floor: a standard-tier client MUST be able to call any endpoint
// (public or non-public) when under the rate limit.
// No global forbids to exclude.
permit (
    principal is ApiClient,
    action == Action::"call",
    resource is Endpoint
)
when {
    principal.tier == "standard"
    && context.requestsThisMinute < 1000
};
