// Floor: an active key with read:invoice scope MUST read an invoice in
// the same organization, regardless of submitted state.
permit (
    principal is ApiKey,
    action == Action::"readInvoice",
    resource is Invoice
)
when {
    principal.organization == resource.organization
    && principal.scopes.contains("read:invoice")
    && context.now.datetime < principal.expiresAt
    && !principal.revoked
};
