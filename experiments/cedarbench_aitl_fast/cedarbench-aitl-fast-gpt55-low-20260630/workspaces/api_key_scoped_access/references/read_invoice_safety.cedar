// Ceiling: readInvoice permitted only when (same org, "read:invoice"
// scope, not expired, not revoked). Reading is allowed even for
// submitted invoices — only writing is restricted by submission state.
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
