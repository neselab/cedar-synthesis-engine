// Ceiling: write is permitted only when the principal is in the
// resource's tenant AND the principal has the admin role. The
// defaultDeny flag is irrelevant for write because admins always pass
// the default-deny gate.
permit (
    principal is User,
    action == Action::"write",
    resource is Document
)
when {
    principal.tenant == resource.tenant
    && principal.role == "admin"
};
