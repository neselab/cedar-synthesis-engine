// Floor: an L3 user MUST be permitted to read a Confidential, non-PII
// document (sidestepping the PII training forbid via !containsPII).
permit (
    principal is User,
    action == Action::"readDocument",
    resource is Document
)
when {
    principal.clearance == "L3"
    && resource.classification == "Confidential"
    && !resource.containsPII
};
