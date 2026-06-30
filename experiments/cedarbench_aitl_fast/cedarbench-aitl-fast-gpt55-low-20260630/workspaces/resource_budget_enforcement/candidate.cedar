permit (
    principal is Tenant,
    action == Action::"create",
    resource is Resource
)
when {
    (principal.tier == "free" && context.usageCount < 5) ||
    (principal.tier == "pro" && context.usageCount < 50) ||
    principal.tier == "enterprise"
};

permit (
    principal is Tenant,
    action == Action::"read",
    resource is Resource
);

permit (
    principal is Tenant,
    action == Action::"delete",
    resource is Resource
);

permit (
    principal is Tenant,
    action == Action::"upgrade",
    resource is Resource
)
when {
    principal.tier == "pro" ||
    principal.tier == "enterprise"
};