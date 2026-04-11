// Floor: an L4 user who is in the document's needToKnow set MUST be
// permitted to read a Restricted, non-PII document (the needToKnow +
// !containsPII combination sidesteps both §8.8 global forbids).
permit (
    principal is User,
    action == Action::"readDocument",
    resource is Document
)
when {
    principal.clearance == "L4"
    && resource.classification == "Restricted"
    && principal in resource.needToKnow
    && !resource.containsPII
};
