// Ceiling: deleteDocument permitted only when (same org, "delete:document"
// scope, not expired, not revoked).
permit (
    principal is ApiKey,
    action == Action::"deleteDocument",
    resource is Document
)
when {
    principal.organization == resource.organization
    && principal.scopes.contains("delete:document")
    && context.now.datetime < principal.expiresAt
    && !principal.revoked
};
