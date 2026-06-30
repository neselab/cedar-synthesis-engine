// Floor: a user who satisfies the view prerequisites (clearance covers
// required_clearance, no compartments_required) AND who holds
// edit_authorized tag containing "true" MUST be permitted to edit.
permit (
    principal is User,
    action == Action::"edit",
    resource is Document
)
when {
    principal.hasTag("clearance")
    && resource.hasTag("required_clearance")
    && principal.getTag("clearance").containsAll(resource.getTag("required_clearance"))
    && !resource.hasTag("compartments_required")
    && principal.hasTag("edit_authorized")
    && principal.getTag("edit_authorized").contains("true")
};
