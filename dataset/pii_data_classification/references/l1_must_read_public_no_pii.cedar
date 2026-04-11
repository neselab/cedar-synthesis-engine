// Floor: an L1 user with PII training MUST be permitted to read a
// Public, non-PII document.
permit (
    principal is User,
    action == Action::"readDocument",
    resource is Document
)
when {
    principal.clearance == "L1"
    && resource.classification == "Public"
    && !resource.containsPII
};
