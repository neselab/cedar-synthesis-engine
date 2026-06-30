// Floor: a user whose adminOf set includes the resource's tenant MUST
// be permitted to delete the resource.
permit (
    principal is User,
    action == Action::"delete",
    resource is Resource
)
when {
    principal.adminOf.contains(resource.tenant)
};
