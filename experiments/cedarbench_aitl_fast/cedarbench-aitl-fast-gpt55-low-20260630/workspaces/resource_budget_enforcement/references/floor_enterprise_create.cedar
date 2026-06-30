// Floor: enterprise tenant MUST always create.
permit (
    principal is Tenant,
    action == Action::"create",
    resource is Resource
)
when {
    principal.tier == "enterprise"
};
