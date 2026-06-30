// Ceiling: readDocument permitted only when ALL of:
//  - same organization,
//  - "read:document" in scopes,
//  - key not expired,
//  - key not revoked.
permit (
    principal is ApiKey,
    action == Action::"readDocument",
    resource is Document
)
when {
    principal.organization == resource.organization
    && principal.scopes.contains("read:document")
    && context.now.datetime < principal.expiresAt
    && !principal.revoked
};
