// Floor: an active key with write:invoice scope MUST write an UNSUBMITTED
// invoice in the same organization. Submitted invoices are excluded by
// the `!resource.submitted` clause per §8.8 floor-bound consistency.
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
