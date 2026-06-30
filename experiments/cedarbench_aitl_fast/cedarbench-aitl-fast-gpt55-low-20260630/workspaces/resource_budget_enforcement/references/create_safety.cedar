// Ceiling: create only within budget per tier.
permit (
    principal is Tenant,
    action == Action::"create",
    resource is Resource
)
when {
    (principal.tier == "free" && context.usageCount < 5)
    || (principal.tier == "pro" && context.usageCount < 50)
    || principal.tier == "enterprise"
};
