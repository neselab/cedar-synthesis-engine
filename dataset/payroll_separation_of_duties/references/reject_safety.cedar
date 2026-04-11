// Ceiling: reject permitted only when (principal is manager or cfo)
// AND entry is in pending_approval. Rejection is not subject to the
// SoD check — clerks cannot reject even their own entries.
permit (
    principal is User,
    action == Action::"reject",
    resource is PayrollEntry
)
when {
    (principal.role == "manager" || principal.role == "cfo")
    && resource.status == "pending_approval"
};
