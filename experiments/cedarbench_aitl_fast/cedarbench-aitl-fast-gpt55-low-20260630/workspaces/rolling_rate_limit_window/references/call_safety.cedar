// Ceiling: a `call` is permitted only when the window snapshot is
// fresh (!windowExpired) AND one of:
//  (1) free tier:       requestsLastMinute < 60   AND requestsLastHour < 1000
//  (2) pro tier:        requestsLastMinute < 600  AND requestsLastHour < 10000
//  (3) enterprise tier: unlimited

// Free tier
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

// Pro tier
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

// Enterprise tier (unlimited rate, but still gated by fresh window)
permit (
    principal is Client,
    action == Action::"call",
    resource is Endpoint
)
when {
    !context.windowExpired
    && principal.tier == "enterprise"
};
