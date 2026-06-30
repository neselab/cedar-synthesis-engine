// Floor: a user whose clearance covers required_clearance AND whose
// compartment set covers compartments_required MUST be permitted to view.
permit (
    principal is User,
    action == Action::"view",
    resource is Document
)
when {
    principal.hasTag("clearance")
    && resource.hasTag("required_clearance")
    && principal.getTag("clearance").containsAll(resource.getTag("required_clearance"))
    && resource.hasTag("compartments_required")
    && principal.hasTag("compartment")
    && principal.getTag("compartment").containsAll(resource.getTag("compartments_required"))
};
