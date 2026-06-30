// Floor: a free-tier client MUST be able to call any endpoint when
// the window is fresh, requestsLastMinute < 60, and
// requestsLastHour < 1000.
permit (
    principal is Client,
    action == Action::"call",
    resource is Endpoint
)
when {
    !context.windowExpired
    && principal.tier == "free"
    && context.requestsLastMinute < 60
    && context.requestsLastHour < 1000
};
