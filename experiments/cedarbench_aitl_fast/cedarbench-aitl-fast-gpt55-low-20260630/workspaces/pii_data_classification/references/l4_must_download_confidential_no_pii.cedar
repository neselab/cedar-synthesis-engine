// Floor: an L4 user MUST be permitted to download a Confidential,
// non-PII document. The one-level-higher download rule makes L4 the
// minimum for Confidential downloads.
permit (
    principal is User,
    action == Action::"downloadDocument",
    resource is Document
)
when {
    principal.clearance == "L4"
    && resource.classification == "Confidential"
    && !resource.containsPII
};
