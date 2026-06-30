// Floor: a user whose clearance covers the document's required_clearance
// MUST be permitted to view, when the document has no compartments_required
// tag. No global forbids in this scenario, so the floor matches the
// ceiling's first branch exactly.
permit (
    principal is User,
    action == Action::"view",
    resource is Document
)
when {
    principal.hasTag("clearance")
    && resource.hasTag("required_clearance")
    && principal.getTag("clearance").containsAll(resource.getTag("required_clearance"))
    && !resource.hasTag("compartments_required")
};
