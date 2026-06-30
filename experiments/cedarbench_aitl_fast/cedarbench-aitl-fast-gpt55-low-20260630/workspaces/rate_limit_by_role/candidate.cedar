permit (
    principal is ApiClient,
    action == Action::"call",
    resource is Endpoint
)
when {
    principal.tier == "free" &&
    resource.isPublic == true &&
    context.requestsThisMinute < 100
};

permit (
    principal is ApiClient,
    action == Action::"call",
    resource is Endpoint
)
when {
    principal.tier == "standard" &&
    context.requestsThisMinute < 1000
};

permit (
    principal is ApiClient,
    action == Action::"call",
    resource is Endpoint
)
when {
    principal.tier == "premium"
};

permit (
    principal is ApiClient,
    action == Action::"bulkCall",
    resource is Endpoint
)
when {
    principal.tier == "premium" &&
    context.requestsThisMinute < 500
};