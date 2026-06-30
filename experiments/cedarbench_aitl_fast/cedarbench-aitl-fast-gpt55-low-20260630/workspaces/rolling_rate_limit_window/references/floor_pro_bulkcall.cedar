// Floor: a pro-tier client MUST be able to bulkCall when the window
// is fresh, the costMultiplier and requestsLastMinute are within
// their declared bounds, and requestsLastMinute * costMultiplier
// <= 1000.
permit (
    principal is Client,
    action == Action::"bulkCall",
    resource is Endpoint
)
when {
    !context.windowExpired
    && principal.tier == "pro"
    && resource.costMultiplier >= 1
    && resource.costMultiplier <= 100
    && context.requestsLastMinute >= 0
    && context.requestsLastMinute <= 1000000
    && context.requestsLastMinute * resource.costMultiplier <= 1000
};
