// Ceiling: deleteResource is permitted only when the principal is in
// the resource's tenant. Cross-tenant deletes are NEVER permitted.
permit (
    principal is User,
    action == Action::"deleteResource",
    resource is Resource
)
when {
    principal.tenant == resource.tenant
};
