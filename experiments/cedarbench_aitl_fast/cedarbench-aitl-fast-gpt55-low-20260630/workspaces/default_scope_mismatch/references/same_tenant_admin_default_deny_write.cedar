// Floor: a tenant admin MUST be permitted to write a document in
// their own tenant EVEN WHEN the tenant is in default-deny mode —
// the admin role is the override of the tenant default at the user
// scope, and write is admin-only regardless of the flag.
permit (
    principal is User,
    action == Action::"write",
    resource is Document
)
when {
    principal.tenant == resource.tenant
    && principal.tenant.defaultDeny
    && principal.role == "admin"
};
