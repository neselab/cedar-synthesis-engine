// Ceiling: call is permitted only when one of:
//  (1) free tier, public endpoint, requestsThisMinute < 100
//  (2) standard tier, requestsThisMinute < 1000
//  (3) premium tier (unlimited)

// Free tier -- public endpoints only, rate-limited at 100/min
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

// Standard tier -- any endpoint, rate-limited at 1000/min
permit (
    principal is ApiClient,
    action == Action::"call",
    resource is Endpoint
)
when {
    principal.tier == "standard"
    && context.requestsThisMinute < 1000
};

// Premium tier -- any endpoint, unlimited
permit (
    principal is ApiClient,
    action == Action::"call",
    resource is Endpoint
)
when {
    principal.tier == "premium"
};
