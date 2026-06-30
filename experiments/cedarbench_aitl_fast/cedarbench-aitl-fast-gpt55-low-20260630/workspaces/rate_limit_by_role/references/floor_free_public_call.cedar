// Floor: a free-tier client MUST be able to call a public endpoint
// when under the rate limit.
// No global forbids to exclude (no forbid rules in this scenario).
permit (
    principal is ApiClient,
    action == Action::"call",
    resource is Endpoint
)
when {
    principal.tier == "free"
    && resource.isPublic
    && context.requestsThisMinute < 100
};
