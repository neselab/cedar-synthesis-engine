// Floor: scoped-admin authority is conferred by adminOf membership, not
// by the role string. A user whose adminOf includes the resource's
// tenant MUST be permitted to view, regardless of what the role string
// happens to be (e.g. role == "viewer" but adminOf includes the tenant
// is still permitted because adminOf is the source of truth).
permit (
    principal is User,
    action == Action::"view",
    resource is Resource
)
when {
    principal.adminOf.contains(resource.tenant)
    && principal.role == "viewer"
};
