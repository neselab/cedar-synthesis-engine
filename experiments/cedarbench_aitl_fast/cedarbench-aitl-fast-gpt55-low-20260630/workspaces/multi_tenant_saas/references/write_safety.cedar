// Ceiling: writeResource is permitted only when the principal is in the
// resource's tenant. Cross-tenant writes are NEVER permitted, regardless
// of global-support status.
permit (
    principal is User,
    action == Action::"writeResource",
    resource is Resource
)
when {
    principal.tenant == resource.tenant
};
