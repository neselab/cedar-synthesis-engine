// Floor: free tenant with < 5 resources MUST create.
permit (
    principal is Tenant,
    action == Action::"create",
    resource is Resource
)
when {
    principal.tier == "free"
    && context.usageCount < 5
};
