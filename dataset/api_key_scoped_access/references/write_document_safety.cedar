// Ceiling: writeDocument permitted only when (same org, "write:document"
// scope, not expired, not revoked).
permit (
    principal is ApiKey,
    action == Action::"writeDocument",
    resource is Document
)
when {
    principal.organization == resource.organization
    && principal.scopes.contains("write:document")
    && context.now.datetime < principal.expiresAt
    && !principal.revoked
};
