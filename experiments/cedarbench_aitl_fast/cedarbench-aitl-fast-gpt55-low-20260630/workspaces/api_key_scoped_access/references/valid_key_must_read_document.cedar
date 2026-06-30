// Floor: an active, non-revoked, non-expired API key with read:document
// scope MUST read a document in the same organization.
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
