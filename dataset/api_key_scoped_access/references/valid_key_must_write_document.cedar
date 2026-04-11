// Floor: an active key with write:document scope MUST write a document
// in the same organization.
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
