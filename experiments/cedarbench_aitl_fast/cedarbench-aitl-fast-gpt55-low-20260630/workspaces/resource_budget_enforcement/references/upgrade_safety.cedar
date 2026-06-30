// Ceiling: upgrade only when pro or enterprise.
permit (
    principal is Tenant,
    action == Action::"upgrade",
    resource is Resource
)
when {
    principal.tier == "pro" || principal.tier == "enterprise"
};
