// Ceiling: a `bulkCall` is permitted only when:
//   - the window snapshot is fresh (!windowExpired)
//   - the costMultiplier and requestsLastMinute are within their
//     spec-declared bounds (so the product cannot overflow)
//   - the tier-specific cost-adjusted budget is satisfied:
//       free:       requestsLastMinute * costMultiplier <= 100
//       pro:        requestsLastMinute * costMultiplier <= 1000
//       enterprise: no budget cap (still requires fresh window + bounds)

// Free tier
permit (
    principal is Client,
    action == Action::"bulkCall",
    resource is Endpoint
)
when {
    !context.windowExpired
    && principal.tier == "free"
    && resource.costMultiplier >= 1
    && resource.costMultiplier <= 100
    && context.requestsLastMinute >= 0
    && context.requestsLastMinute <= 1000000
    && context.requestsLastMinute * resource.costMultiplier <= 100
};

// Pro tier
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

// Enterprise tier
permit (
    principal is Client,
    action == Action::"bulkCall",
    resource is Endpoint
)
when {
    !context.windowExpired
    && principal.tier == "enterprise"
    && resource.costMultiplier >= 1
    && resource.costMultiplier <= 100
    && context.requestsLastMinute >= 0
    && context.requestsLastMinute <= 1000000
};
