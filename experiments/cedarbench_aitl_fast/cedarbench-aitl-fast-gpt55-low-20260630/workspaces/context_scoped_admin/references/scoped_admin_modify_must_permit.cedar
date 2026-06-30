// Floor: a user whose adminOf set includes the resource's tenant MUST
// be permitted to modify the resource.
permit (
    principal is User,
    action == Action::"modify",
    resource is Resource
)
when {
    principal.adminOf.contains(resource.tenant)
};
