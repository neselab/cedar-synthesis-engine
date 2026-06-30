permit (
    principal is Client,
    action == Action::"call",
    resource is Endpoint
)
when {
    context.windowExpired == false &&
    (
        (
            principal.tier == "free" &&
            context.requestsLastMinute < 60 &&
            context.requestsLastHour < 1000
        ) ||
        (
            principal.tier == "pro" &&
            context.requestsLastMinute < 600 &&
            context.requestsLastHour < 10000
        ) ||
        principal.tier == "enterprise"
    )
};

permit (
    principal is Client,
    action == Action::"bulkCall",
    resource is Endpoint
)
when {
    context.windowExpired == false &&
    resource.costMultiplier >= 1 &&
    resource.costMultiplier <= 100 &&
    context.requestsLastMinute >= 0 &&
    context.requestsLastMinute <= 1000000 &&
    principal.tier == "free" &&
    context.requestsLastMinute * resource.costMultiplier <= 100
};

permit (
    principal is Client,
    action == Action::"bulkCall",
    resource is Endpoint
)
when {
    context.windowExpired == false &&
    resource.costMultiplier >= 1 &&
    resource.costMultiplier <= 100 &&
    context.requestsLastMinute >= 0 &&
    context.requestsLastMinute <= 1000000 &&
    principal.tier == "pro" &&
    context.requestsLastMinute * resource.costMultiplier <= 1000
};

permit (
    principal is Client,
    action == Action::"bulkCall",
    resource is Endpoint
)
when {
    context.windowExpired == false &&
    resource.costMultiplier >= 1 &&
    resource.costMultiplier <= 100 &&
    context.requestsLastMinute >= 0 &&
    context.requestsLastMinute <= 1000000 &&
    principal.tier == "enterprise"
};