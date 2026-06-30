// Floor: a tenant admin MUST be permitted to write a document in
// their own tenant when the tenant is NOT in default-deny mode.
permit (
    principal is User,
    action == Action::"write",
    resource is Document
)
when {
    principal.tenant == resource.tenant
    && !principal.tenant.defaultDeny
    && principal.role == "admin"
};
