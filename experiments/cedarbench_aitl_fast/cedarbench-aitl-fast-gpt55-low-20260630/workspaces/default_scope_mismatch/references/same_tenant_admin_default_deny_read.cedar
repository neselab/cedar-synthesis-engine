// Floor: a tenant admin MUST be permitted to read a document in
// their own tenant EVEN WHEN the tenant is in default-deny mode. This
// is the user-scope admin override of the tenant-scope default.
permit (
    principal is User,
    action == Action::"read",
    resource is Document
)
when {
    principal.tenant == resource.tenant
    && principal.tenant.defaultDeny
    && principal.role == "admin"
};
