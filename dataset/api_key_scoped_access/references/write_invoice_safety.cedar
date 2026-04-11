// Ceiling: writeInvoice permitted only when (same org, "write:invoice"
// scope, not expired, not revoked, NOT submitted). Submitted invoices
// are immutable even with write scope.
permit (
    principal is ApiKey,
    action == Action::"writeInvoice",
    resource is Invoice
)
when {
    principal.organization == resource.organization
    && principal.scopes.contains("write:invoice")
    && context.now.datetime < principal.expiresAt
    && !principal.revoked
    && !resource.submitted
};
