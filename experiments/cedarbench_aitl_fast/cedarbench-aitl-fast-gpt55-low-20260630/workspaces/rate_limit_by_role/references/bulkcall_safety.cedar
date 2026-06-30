// Ceiling: bulkCall is permitted only when premium tier AND
// requestsThisMinute < 500.
permit (
    principal is ApiClient,
    action == Action::"bulkCall",
    resource is Endpoint
)
when {
    principal.tier == "premium"
    && context.requestsThisMinute < 500
};
