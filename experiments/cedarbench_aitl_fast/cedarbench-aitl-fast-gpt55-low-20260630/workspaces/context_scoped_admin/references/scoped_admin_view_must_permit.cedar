// Floor: a user whose adminOf set includes the resource's tenant MUST
// be permitted to view the resource. No additional gating.
permit (
    principal is User,
    action == Action::"view",
    resource is Resource
)
when {
    principal.adminOf.contains(resource.tenant)
};
