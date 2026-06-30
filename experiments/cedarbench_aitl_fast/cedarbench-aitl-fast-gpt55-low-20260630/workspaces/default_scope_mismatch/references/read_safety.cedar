// Ceiling: read is permitted only when the principal is in the
// resource's tenant AND either the tenant is not in default-deny mode
// OR the principal has the admin role (the user-scope override).
permit (
    principal is User,
    action == Action::"read",
    resource is Document
)
when {
    principal.tenant == resource.tenant
    && (!principal.tenant.defaultDeny || principal.role == "admin")
};
