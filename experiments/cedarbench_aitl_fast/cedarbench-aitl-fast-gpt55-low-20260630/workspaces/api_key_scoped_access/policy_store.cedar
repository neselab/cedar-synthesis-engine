// Policy store — verified policies appended here

// --- Verified (eval iteration 1) ---
forbid (
    principal is ApiKey,
    action in [
        Action::"readDocument",
        Action::"writeDocument",
        Action::"deleteDocument",
        Action::"readInvoice",
        Action::"writeInvoice"
    ],
    resource
)
when {
    context.now.datetime >= principal.expiresAt
};

forbid (
    principal is ApiKey,
    action in [
        Action::"readDocument",
        Action::"writeDocument",
        Action::"deleteDocument",
        Action::"readInvoice",
        Action::"writeInvoice"
    ],
    resource
)
when {
    principal.revoked == true
};

forbid (
    principal is ApiKey,
    action == Action::"writeInvoice",
    resource is Invoice
)
when {
    resource.submitted == true
};

permit (
    principal is ApiKey,
    action == Action::"readDocument",
    resource is Document
)
when {
    principal.organization == resource.organization &&
    principal.scopes.contains("read:document")
};

permit (
    principal is ApiKey,
    action == Action::"writeDocument",
    resource is Document
)
when {
    principal.organization == resource.organization &&
    principal.scopes.contains("write:document")
};

permit (
    principal is ApiKey,
    action == Action::"deleteDocument",
    resource is Document
)
when {
    principal.organization == resource.organization &&
    principal.scopes.contains("delete:document")
};

permit (
    principal is ApiKey,
    action == Action::"readInvoice",
    resource is Invoice
)
when {
    principal.organization == resource.organization &&
    principal.scopes.contains("read:invoice")
};

permit (
    principal is ApiKey,
    action == Action::"writeInvoice",
    resource is Invoice
)
when {
    principal.organization == resource.organization &&
    principal.scopes.contains("write:invoice")
};
