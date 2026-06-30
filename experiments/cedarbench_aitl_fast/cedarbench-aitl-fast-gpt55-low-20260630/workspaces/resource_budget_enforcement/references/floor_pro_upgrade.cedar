// Floor: pro tenant MUST upgrade.
permit (
    principal is Tenant,
    action == Action::"upgrade",
    resource is Resource
)
when {
    principal.tier == "pro"
};
