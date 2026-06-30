// Floor: a pro-tier client MUST be able to call any endpoint when
// the window is fresh, requestsLastMinute < 600, and
// requestsLastHour < 10000.
permit (
    principal is Client,
    action == Action::"call",
    resource is Endpoint
)
when {
    !context.windowExpired
    && principal.tier == "pro"
    && context.requestsLastMinute < 600
    && context.requestsLastHour < 10000
};
